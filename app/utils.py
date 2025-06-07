import os
import json
import time
import redis
from datetime import datetime
import logging # Import logging


from model import db
from model.upstream_check_log import UpstreamCheckLog
from model.upstream_cache import UpstreamCache
from model.redirect import Redirect
from app import CONSTANTS # Import CONSTANTS for data source strings

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Ensure data directory exists (cross-platform)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, 'redirect.config.json')

# --- JSON config helpers ---
def _load_config():
    if not os.path.exists(CONFIG_FILE):
        import secrets
        import string
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        logger.info(f"Generated password for admin access. Please check your console for the password if running for the first time.")
        logger.info(f"Admin Password: {random_pwd}") # Log it at INFO level for visibility during first run
        default = {
            "port": 80,
            "auto_redirect_delay": 3,
            "database":"sqlite:///redirects.db",
            "admin_password": random_pwd,
            "delete_requires_password": True,
            "upstreams": [],
            "redis": {
                "enabled": True,
                "host": "redis",
                "port": 6379
            },
            "upstream_cache": {
                "enabled": True
            }
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default, f, indent=2)
            logger.info(f"Created default configuration file: {CONFIG_FILE}")
        except IOError as e:
            logger.error(f"Failed to create default config file {CONFIG_FILE}: {e}")
        return default
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.exception(f"Error loading configuration file {CONFIG_FILE}. Using empty config.")
        return {} # Return empty config on error

def get_db_uri():
    cfg=_load_config()
    if "database" in cfg:
        db_url=cfg["database"]
        return db_url
    logger.warning("Database URI not found in config, defaulting to sqlite:///redirects.db")
    return "sqlite:///redirects.db"

def _save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
        logger.debug(f"Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        logger.error(f"Failed to save configuration file {CONFIG_FILE}: {e}")


def get_config(key, default=None):
    cfg = _load_config()
    if key in cfg:
        return cfg[key]
    # Set and return default if not present
    cfg[key] = default
    _save_config(cfg)
    logger.info(f"Config key '{key}' not found, set to default: {default}")
    return default

def set_config(key, value):
    cfg = _load_config()
    cfg[key] = value
    _save_config(cfg)
    logger.info(f"Config key '{key}' set to '{value}'")


# --- SQLAlchemy schema setup (no direct ALTER TABLE needed with Flask-Migrate) ---
def ensure_access_count_column(db_session):
    logger.debug("Skipping ensure_access_count_column (handled by Flask-Migrate).")
    pass

def ensure_audit_columns(db_session):
    logger.debug("Skipping ensure_audit_columns (handled by Flask-Migrate).")
    pass


def get_admin_password():
    pwd = get_config('admin_password')
    if pwd:
        return pwd
    import secrets
    import string
    pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    set_config('admin_password', pwd)
    logger.warning("Admin password was not set in config. Generated a new one.")
    return pwd

def get_port():
    port = get_config('port')
    if port:
        return port
    set_config('port', 80)
    logger.info("Port not set in config, defaulting to 80.")
    return 80

def get_auto_redirect_delay():
    delay = get_config('auto_redirect_delay')
    if delay is not None:
        return delay
    set_config('auto_redirect_delay', 0)
    logger.info("Auto redirect delay not set, defaulting to 0.")
    return 0

def get_delete_requires_password():
    val = get_config('delete_requires_password')
    if val is not None:
        return val
    set_config('delete_requires_password', True)
    logger.info("Delete requires password not set, defaulting to True.")
    return True

# --- Access count helpers ---
def increment_access_count(pattern):
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    if redirect_obj:
        redirect_obj.access_count = (redirect_obj.access_count or 0) + 1
        db.session.commit()
        logger.info(f"Access count incremented for shortcut '{pattern}'. New count: {redirect_obj.access_count}")
        # Invalidate Redis cache for this shortcut after update
        if _redis_enabled:
            redis_delete(f"shortcut:{pattern}")
    else:
        logger.warning(f"Attempted to increment access count for non-existent shortcut: '{pattern}'")


def get_access_count(pattern):
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    count = redirect_obj.access_count if redirect_obj else 0
    logger.debug(f"Retrieved access count for '{pattern}': {count}")
    return count

# Helper to get created/updated times for UI
def get_created_updated(pattern):
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    if redirect_obj:
        logger.debug(f"Retrieved audit info for '{pattern}'.")
        return redirect_obj.created_at, redirect_obj.updated_at
    logger.warning(f"Could not retrieve audit info for non-existent shortcut: '{pattern}'")
    return None, None

def log_upstream_check(pattern, upstream_name, check_url, result, detail, tried_at):
    log_entry = UpstreamCheckLog(
        pattern=pattern,
        upstream_name=upstream_name,
        check_url=check_url,
        result=result,
        detail=detail,
        tried_at=tried_at # This is already an ISO string
    )
    db.session.add(log_entry)
    db.session.commit()
    logger.info(f"Upstream check logged: pattern='{pattern}', upstream='{upstream_name}', result='{result}'")

def get_upstream_logs():
    # Order by id descending to get latest logs first
    logs = UpstreamCheckLog.query.order_by(UpstreamCheckLog.id.desc()).all()
    logger.debug(f"Retrieved {len(logs)} upstream check logs.")
    # Convert SQLAlchemy objects to dictionaries for easier template rendering
    return [{
        'id': log.id,
        'pattern': log.pattern,
        'upstream_name': log.upstream_name,
        'check_url': log.check_url,
        'result': log.result,
        'detail': log.detail,
        'tried_at': log.tried_at,
        'count': log.count
    } for log in logs]

# --- Redis helpers ---
_redis_client = None
_redis_enabled = False
_redis_host = 'localhost'
_redis_port = 6379

def init_redis_from_config():
    global _redis_client, _redis_enabled, _redis_host, _redis_port
    cfg = _load_config()
    redis_cfg = cfg.get('redis', {})
    _redis_enabled = redis_cfg.get('enabled', False)
    _redis_host = redis_cfg.get('host', 'redis') # Default to 'redis' for Docker
    _redis_port = redis_cfg.get('port', 6379)
    if _redis_enabled:
        try:
            _redis_client = redis.Redis(host=_redis_host, port=_redis_port, decode_responses=True, socket_connect_timeout=1) # Added timeout
            _redis_client.ping()
            logger.info(f"Redis enabled and connected: host={_redis_host}, port={_redis_port}")
        except redis.exceptions.ConnectionError as e:
            logger.warning(f"Redis config enabled but connection failed to '{_redis_host}:{_redis_port}': {e}. Redis functionality disabled.")
            _redis_enabled = False
        except Exception as e:
            logger.exception(f"Unexpected error initializing Redis. Redis functionality disabled.")
            _redis_enabled = False
    else:
        logger.info("Redis is disabled (see config).")

def redis_get(key):
    if _redis_enabled and _redis_client:
        try:
            value = _redis_client.get(key)
            logger.debug(f"Redis GET '{key}': {'HIT' if value else 'MISS'}")
            return value
        except Exception as e:
            logger.error(f"Redis GET failed for key '{key}': {e}")
            return None
    logger.debug(f"Redis GET '{key}': Skipped (Redis disabled/not connected).")
    return None

def redis_set(key, value, ex=None): # Added optional expiry 'ex'
    if _redis_enabled and _redis_client:
        try:
            _redis_client.set(key, value, ex=ex)
            logger.debug(f"Redis SET '{key}' successfully.")
        except Exception as e:
            logger.error(f"Redis SET failed for key '{key}': {e}")
            pass
    else:
        logger.debug(f"Redis SET '{key}': Skipped (Redis disabled/not connected).")

def redis_delete(key):
    if _redis_enabled and _redis_client:
        try:
            _redis_client.delete(key)
            logger.debug(f"Redis DELETE '{key}' successfully.")
        except Exception as e:
            logger.error(f"Redis DELETE failed for key '{key}': {e}")
            pass
    else:
        logger.debug(f"Redis DELETE '{key}': Skipped (Redis disabled/not connected).")


def get_shortcut(pattern):
    start_time = time.time()
    shortcut = None
    source = CONSTANTS.data_source_redis # Default source assumption

    if _redis_enabled:
        val = redis_get(f"shortcut:{pattern}")
        if val:
            try:
                shortcut = json.loads(val)
                # Ensure data_type is present for consistency, if not already
                if 'data_type' not in shortcut:
                    shortcut['data_type'] = shortcut.get('type', CONSTANTS.DATA_TYPE_STATIC)
                logger.debug(f"Shortcut '{pattern}' HIT from Redis. Source: {source}")
                return shortcut, source, round(time.time() - start_time, 6)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from Redis for shortcut:{pattern}: {e}. Deleting corrupt entry.")
                redis_delete(f"shortcut:{pattern}") # If cached data is corrupt, delete it
            except Exception as e:
                logger.exception(f"Unexpected error processing Redis shortcut:{pattern}. Deleting entry.")
                redis_delete(f"shortcut:{pattern}") # Delete if other unexpected error

    # Fallback to DB (and hydrate Redis if enabled)
    source = CONSTANTS.data_source_redirect
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    if redirect_obj:
        shortcut = {
            'pattern': redirect_obj.pattern,
            'type': redirect_obj.type,
            'target': redirect_obj.target,
            'access_count': redirect_obj.access_count if redirect_obj.access_count is not None else 0,
            'created_at': redirect_obj.created_at,
            'updated_at': redirect_obj.updated_at,
            'data_type': redirect_obj.type # Assuming 'type' maps to CONSTANTS.DATA_TYPE_STATIC/DYNAMIC
        }
        # Hydrate Redis
        if _redis_enabled:
            try:
                redis_set(f"shortcut:{pattern}", json.dumps(shortcut))
                logger.debug(f"Shortcut '{pattern}' MISS from Redis, HIT from DB. Hydrated Redis.")
            except Exception as e:
                logger.error(f"Failed to hydrate Redis with shortcut:{pattern}: {e}")
        else:
            logger.debug(f"Shortcut '{pattern}' HIT from DB (Redis disabled).")
        return shortcut, source, round(time.time() - start_time, 6)

    # Check upstream DB cache (and hydrate Redis if enabled)
    source = CONSTANTS.data_source_upstream
    if is_upstream_cache_enabled():
        cached_upstream_result = get_cached_upstream_result_from_db(pattern=pattern)
        if cached_upstream_result:
            # Add data_type to cached result for consistency with local shortcuts
            cached_upstream_result['data_type'] = CONSTANTS.DATA_TYPE_STATIC
            # Hydrate Redis with the upstream cache result (already handled by get_cached_upstream_result_from_db)
            logger.debug(f"Upstream shortcut '{pattern}' HIT from cache (Redis/DB).")
            return cached_upstream_result, source, round(time.time() - start_time, 6)
        logger.debug(f"Upstream shortcut '{pattern}' not found in cache.")

    logger.info(f"Shortcut '{pattern}' not found in local DB or upstream cache.")
    return None, None, round(time.time() - start_time, 6)

def set_shortcut(pattern, type_, target, access_count=0, created_at=None, updated_at=None, created_ip=None, updated_ip=None):
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    if redirect_obj:
        # Update existing shortcut
        redirect_obj.type = type_
        redirect_obj.target = target
        # Only update access_count if explicitly provided, otherwise retain current
        if access_count is not None:
             redirect_obj.access_count = access_count
        redirect_obj.updated_at = updated_at or datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        redirect_obj.updated_ip = updated_ip
        logger.info(f"Updated existing shortcut: '{pattern}'")
    else:
        # Create new shortcut
        new_shortcut = Redirect(
            pattern=pattern,
            type=type_,
            target=target,
            access_count=access_count,
            created_at=created_at or datetime.utcnow().isoformat(sep=' ', timespec='seconds'),
            updated_at=updated_at or datetime.utcnow().isoformat(sep=' ', timespec='seconds'),
            created_ip=created_ip,
            updated_ip=updated_ip
        )
        db.session.add(new_shortcut)
        logger.info(f"Created new shortcut: '{pattern}'")

    try:
        db.session.commit()
        logger.debug(f"DB commit successful for shortcut '{pattern}'.")
        # Invalidate (or re-set) Redis cache for this shortcut after update/set
        if _redis_enabled:
            # Fetch the updated shortcut from DB to ensure consistency before caching
            updated_shortcut = Redirect.query.filter_by(pattern=pattern).first()
            if updated_shortcut:
                shortcut_data = {
                    'pattern': updated_shortcut.pattern,
                    'type': updated_shortcut.type,
                    'target': updated_shortcut.target,
                    'access_count': updated_shortcut.access_count if updated_shortcut.access_count is not None else 0,
                    'created_at': updated_shortcut.created_at,
                    'updated_at': updated_shortcut.updated_at,
                    'data_type': updated_shortcut.type
                }
                redis_set(f"shortcut:{pattern}", json.dumps(shortcut_data))
                logger.debug(f"Redis cache updated for shortcut '{pattern}'.")
        else:
            logger.debug(f"Redis cache not updated for '{pattern}' (Redis disabled).")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to set/update shortcut '{pattern}' in DB. Rolled back transaction.")
        raise # Re-raise the exception after logging for proper error handling upstream


# --- Upstream Cache helpers ---
def init_upstream_cache_table(db_session):
    logger.debug("Skipping init_upstream_cache_table (handled by Flask-Migrate).")
    pass


def is_upstream_cache_enabled():
    cfg = _load_config()
    enabled = cfg.get('upstream_cache', {}).get('enabled', True)
    logger.debug(f"Upstream cache enabled status: {enabled}")
    return enabled

def cache_upstream_result(pattern, upstream_name, resolved_url, checked_at):
    cache_entry = UpstreamCache.query.filter_by(
        pattern=pattern,
        upstream_name=upstream_name
    ).first()

    if cache_entry:
        cache_entry.resolved_url = resolved_url
        cache_entry.checked_at = checked_at
        logger.info(f"Updated upstream cache for '{pattern}' in '{upstream_name}'.")
    else:
        new_cache_entry = UpstreamCache(
            pattern=pattern,
            upstream_name=upstream_name,
            resolved_url=resolved_url,
            checked_at=checked_at
        )
        db.session.add(new_cache_entry)
        logger.info(f"Created new upstream cache entry for '{pattern}' in '{upstream_name}'.")
    try:
        db.session.commit()
        logger.debug(f"DB commit successful for upstream cache '{pattern}'.")
        # Also update Redis cache for single pattern lookup (cache-aside for main lookup)
        if _redis_enabled:
            redis_set(f"upstream_cache:{pattern}", json.dumps({
                'pattern': pattern,
                'upstream_name': upstream_name,
                'resolved_url': resolved_url,
                'checked_at': checked_at
            }))
            logger.debug(f"Redis cache updated for upstream_cache:'{pattern}'.")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to cache upstream result for '{pattern}' in '{upstream_name}'. Rolled back transaction.")
        raise


def get_cached_upstream_result(pattern):
    # This function primarily attempts to get from Redis,
    # then calls the DB specific one if not found in Redis,
    # which in turn hydrates Redis.
    if _redis_enabled:
        val = redis_get(f"upstream_cache:{pattern}")
        if val:
            try:
                result = json.loads(val)
                logger.debug(f"Upstream cache HIT from Redis for '{pattern}'.")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from Redis for upstream_cache:{pattern}: {e}. Deleting corrupt entry.")
                redis_delete(f"upstream_cache:{pattern}") # Delete corrupt entry
            except Exception as e:
                logger.exception(f"Unexpected error processing Redis upstream_cache:{pattern}. Deleting entry.")
                redis_delete(f"upstream_cache:{pattern}")
    # If not in Redis or error, get from DB, which will then hydrate Redis
    logger.debug(f"Upstream cache MISS from Redis for '{pattern}', checking DB.")
    return get_cached_upstream_result_from_db(pattern)

def get_cached_upstream_result_from_db(pattern):
    # This private helper explicitly gets from DB and hydrates Redis.
    cache_entry = UpstreamCache.query.filter_by(pattern=pattern).first()
    if cache_entry:
        result = {
            'pattern': cache_entry.pattern,
            'upstream_name': cache_entry.upstream_name,
            'resolved_url': cache_entry.resolved_url,
            'checked_at': cache_entry.checked_at
        }
        # Hydrate Redis
        if _redis_enabled:
            try:
                redis_set(f"upstream_cache:{pattern}", json.dumps(result))
                logger.debug(f"Upstream cache HIT from DB for '{pattern}'. Hydrated Redis.")
            except Exception as e:
                logger.error(f"Failed to hydrate Redis with upstream_cache:{pattern}: {e}")
        else:
            logger.debug(f"Upstream cache HIT from DB for '{pattern}' (Redis disabled).")
        return result
    logger.debug(f"Upstream cache not found in DB for '{pattern}'.")
    return None

def list_upstream_cache(upstream_name):
    cached_entries = UpstreamCache.query.filter_by(upstream_name=upstream_name).order_by(UpstreamCache.checked_at.desc()).all()
    logger.debug(f"Listed {len(cached_entries)} upstream cache entries for '{upstream_name}'.")
    # No Redis hydration here, as this is a list retrieval, not a single key lookup
    return [
        {'pattern': entry.pattern, 'resolved_url': entry.resolved_url, 'checked_at': entry.checked_at}
        for entry in cached_entries
    ]

def clear_upstream_cache(pattern):
    # Delete from DB
    num_deleted = UpstreamCache.query.filter_by(pattern=pattern).delete()
    db.session.commit()
    logger.info(f"Cleared {num_deleted} upstream cache entries from DB for '{pattern}'.")
    # Delete from Redis
    if _redis_enabled:
        try:
            redis_delete(f"upstream_cache:{pattern}")
            logger.debug(f"Cleared upstream cache entry from Redis for '{pattern}'.")
        except Exception as e:
            logger.error(f"Redis DELETE failed for upstream_cache:{pattern}: {e}")

def app_startup_banner(app=None):
    import platform
    ascii_art = r''' _______  _______  ______  _________ _______  _______  _______ _________ _______  _______
(  ____ )(  ____ \\  __  \\ \__   __/(  ____ )(  ____ \\  ____ \\__   __/(  ___  )(  ____ )
| (    )|| (    \/| (  \  )   ) (   | (    )|| (    \/| (    \/   ) (   | (   ) || (    )|
| (____)|| (__    | |   ) |   | |   | (____)|| (__    | |         | |   | |   | || (____)|
|     __)|  __)   | |   | |   | |   |     __)|  __)   | |         | |   | |   | ||     __)
| (\ (   | (      | |   ) |   | |   | (\ (   | (      | |         | |   | |   | || (\ (
| ) \ \__| (____/\\| (__/  )___) (___| ) \ \__| (____/\\| (____/\\   | |   | (___) || ) \ \__
|/   \__/(_______/(______/ \_______/|/   \__/(_______/(_______/   )_(   (_______)|/   \__/

'''
    logger.info("\n" + ascii_art) # Log the banner
    logger.info("==============================\n   GUNICORN MODE - READY\n==============================")
    logger.info("URL Shortener & Redirector app initialized.")
    if app is not None:
        logger.info(f"Configured to run on port: {app.config.get('port', 'unknown')}")
    else:
        logger.info("(Port unknown: app not provided)")
    # Detect OS and print instructions for host file entry
    os_name = platform.system().lower()
    logger.info("\n==============================")
    logger.info(f"Detected OS: {os_name.capitalize()}")
    logger.info("==============================\n")
    if os_name == "windows":
        logger.info("Run the following command in PowerShell as Administrator:")
        logger.info("  .\\scripts\\add-r-host-windows.ps1")
        logger.info("Or manually add this line to C:\\Windows\\System32\\drivers\\etc\\hosts:")
        logger.info("  127.0.0.1   r\n")
    elif os_name == "darwin":
        logger.info("Run the following command in Terminal:")
        logger.info("  bash scripts/add-r-host-macos.sh")
        logger.info("Or manually edit /etc/hosts using:")
        logger.info("  sudo nano /etc/hosts")
        logger.info("Then add this line:")
        logger.info("  127.0.0.1   r\n")
        logger.info("Run `dscacheutil -flushcache && sudo killall -HUP mDNSResponder` to apply changes.\n")
    elif os_name == "linux":
        logger.info("Run the following command in Terminal:")
        logger.info("  bash scripts/add-r-host-linux.sh")
        logger.info("Or manually edit /etc/hosts using:")
        logger.info("  sudo nano /etc/hosts")
        logger.info("Then add this line:")
        logger.info("  127.0.0.1   r\n")
    else:
        logger.info("Your OS is not explicitly supported. Please manually update your hosts file:\n")
        logger.info("  127.0.0.1   r")
    # Print Redis status
    if _redis_enabled:
        logger.info(f"Redis enabled: host={_redis_host}, port={_redis_port}")
    else:
        logger.info("Redis is disabled (see config)")

    # Check if 'r' hostname resolves to localhost
    import socket
    try:
        r_ip = socket.gethostbyname('r')
        if r_ip == '127.0.0.1':
            logger.info("Hostname 'r' resolves to 127.0.0.1 (OK)")
        else:
            logger.warning(f"Hostname 'r' resolves to {r_ip} (not 127.0.0.1). Check your hosts/DNS setup.")
    except socket.gaierror: # Specific exception for name resolution failures
        logger.warning("Hostname 'r' does not resolve. Add '127.0.0.1   r' to your hosts file or set up DNS.")
    except Exception as e:
        logger.exception(f"Unexpected error checking hostname 'r' resolution: {e}")

    # Docker environment and port/network info
    running_in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')
    if running_in_docker:
        logger.info("[INFO] Running inside a Docker container.")
        logger.info("      The app listens on the internal container port (default 80).\n      To access externally, ensure you map the container port to a host port using '-p <host_port>:80' in Docker.")
        logger.info("      If using Docker Compose or custom networks, check your port mappings and network mode.")
    else:
        logger.info("Not running in Docker. If using Docker, make sure to map ports correctly.")


def get_db():
    logger.debug("Returning SQLAlchemy DB instance.")
    return db

# GET/POST: Delete shortcut. Triggered when user visits /delete/<subpath> or submits delete confirmation.
def deleteShortCut(pattern):
    redirect_obj = Redirect.query.filter_by(pattern=pattern).first()
    if redirect_obj:
        db.session.delete(redirect_obj)
        try:
            db.session.commit()
            logger.info(f"Deleted shortcut: '{pattern}'")
            # Invalidate Redis cache for this shortcut
            if _redis_enabled:
                redis_delete(f"shortcut:{pattern}")
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Failed to delete shortcut '{pattern}'. Rolled back transaction.")
            raise # Re-raise after logging
    else:
        logger.warning(f"Attempted to delete non-existent shortcut: '{pattern}'")


# check redirect db and return true or false if any pattern exist:
def isPatternExists(subpath):
    exists = Redirect.query.filter_by(pattern=subpath).first() is not None
    logger.debug(f"Checking if shortcut '{subpath}' exists: {exists}")
    return exists


def import_redirects_from_json(json_data):
    """
    Imports redirect data from a JSON list.
    Clears existing redirects, imports new ones, and clears Redis cache.

    Args:
        json_data (list): A list of dictionaries, each representing a redirect.

    Returns:
        dict: A dictionary with 'success' (bool), 'message' (str), and 'imported_count' (int, optional).
    """
    try:
        if not isinstance(json_data, list):
            logger.error("Import failed: JSON data is not a list.")
            return {'success': False, 'message': 'Invalid JSON data format: expected a list of redirects.'}

        # Clear existing redirects
        db.session.query(Redirect).delete()
        db.session.commit()
        logger.info("Cleared existing redirects from DB before import.")

        imported_count = 0
        for entry in json_data:
            # Basic validation: ensure 'pattern', 'type', 'target' are present,
            # though get() with defaults handles missing keys gracefully.
            if not entry.get('pattern') or not entry.get('target'):
                logger.warning(f"Skipping malformed entry during import: {entry}")
                continue  # Skip malformed entries

            new_redirect = Redirect(
                pattern=entry.get('pattern'),
                type=entry.get('type', CONSTANTS.DATA_TYPE_STATIC),
                target=entry.get('target'),
                access_count=entry.get('access_count', 0),
                created_at=entry.get('created_at', datetime.utcnow().isoformat(sep=' ', timespec='seconds')),
                updated_at=entry.get('updated_at', datetime.utcnow().isoformat(sep=' ', timespec='seconds')),
                created_ip=entry.get('created_ip', 'import'),
                updated_ip=entry.get('updated_ip', 'import')
            )
            db.session.add(new_redirect)
            imported_count += 1

        db.session.commit()
        logger.info(f"Imported {imported_count} redirects successfully into DB.")

        # Clear Redis cache if enabled
        if _redis_enabled:
            # Get the _redis_client instance from utils (already defined globally in utils)
            global _redis_client
            if _redis_client:
                try:
                    keys_to_delete = _redis_client.keys('shortcut:*')
                    if keys_to_delete:
                        _redis_client.delete(*keys_to_delete)
                        logger.info(f"Cleared {len(keys_to_delete)} shortcut caches from Redis after import.")
                    else:
                        logger.debug("No shortcut keys found in Redis to clear after import.")
                except Exception as e:
                    logger.error(f"Failed to clear Redis shortcut cache after import: {e}")
            else:
                logger.warning("Redis client not available, skipped clearing shortcut cache after import.")
        else:
            logger.debug("Redis is disabled, skipped clearing shortcut cache after import.")

        return {'success': True, 'message': f'Redirect data imported successfully. {imported_count} records imported.',
                'imported_count': imported_count}

    except (json.JSONDecodeError, ValueError) as e:
        db.session.rollback()
        logger.error(f"Import failed due to JSON/ValueError: {e}")
        return {'success': False, 'message': f'Import failed: Invalid JSON file or data format: {e}'}
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error during redirect import.")
        return {'success': False, 'message': f'Import failed: An unexpected error occurred: {e}'}
