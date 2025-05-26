import os
import sqlite3
import json
from flask import g
import redis

# Ensure data directory exists (cross-platform)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE = os.path.join(DATA_DIR, 'redirects.db')
CONFIG_FILE = os.path.join(DATA_DIR, 'redirect.config.json')

# --- JSON config helpers ---
def _load_config():
    if not os.path.exists(CONFIG_FILE):
        import secrets
        import string
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        print(f"Generated password :{random_pwd} for admin access")
        default = {
            "port": 80,
            "auto_redirect_delay": 3,
            "admin_password": random_pwd,
            "delete_requires_password": True,
            "upstreams": [],
            "redis": {
                "enabled": True,
                "host": "localhost",
                "port": 6379
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f, indent=2)
        return default
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def _save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def get_config(key, default=None):
    cfg = _load_config()
    if key in cfg:
        return cfg[key]
    # Set and return default if not present
    cfg[key] = default
    _save_config(cfg)
    return default

def set_config(key, value):
    cfg = _load_config()
    cfg[key] = value
    _save_config(cfg)

# --- Add access_count to schema if missing ---
def ensure_access_count_column(db):
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN access_count INTEGER DEFAULT 0')
        db.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

# --- Add columns for audit logging if missing ---
def ensure_audit_columns(db):
    # Add created_at
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN created_at TEXT')
        db.commit()
    except sqlite3.OperationalError:
        pass
    # Add updated_at
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN updated_at TEXT')
        db.commit()
    except sqlite3.OperationalError:
        pass
    # Add created_ip
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN created_ip TEXT')
        db.commit()
    except sqlite3.OperationalError:
        pass
    # Add updated_ip
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN updated_ip TEXT')
        db.commit()
    except sqlite3.OperationalError:
        pass

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        ensure_access_count_column(db)
        ensure_audit_columns(db)
    return db

def get_admin_password():
    pwd = get_config('admin_password')
    if pwd:
        return pwd
    import secrets
    import string
    pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    set_config('admin_password', pwd)
    return pwd

def get_port():
    port = get_config('port')
    if port:
        return port
    set_config('port', 80)
    return 80

def get_auto_redirect_delay():
    delay = get_config('auto_redirect_delay')
    if delay is not None:
        return delay
    set_config('auto_redirect_delay', 0)
    return 0

def get_delete_requires_password():
    val = get_config('delete_requires_password')
    if val is not None:
        return val
    set_config('delete_requires_password', True)
    return True

# --- Access count helpers ---
def increment_access_count(pattern):
    db = get_db()
    db.execute('UPDATE redirects SET access_count = COALESCE(access_count, 0) + 1 WHERE pattern=?', (pattern,))
    db.commit()

def get_access_count(pattern):
    db = get_db()
    cursor = db.execute('SELECT access_count FROM redirects WHERE pattern=?', (pattern,))
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 0

# Helper to get created/updated times for UI
def get_created_updated(pattern):
    db = get_db()
    cursor = db.execute('SELECT created_at, updated_at FROM redirects WHERE pattern=?', (pattern,))
    row = cursor.fetchone()
    if row:
        return row[0], row[1]
    return None, None

# --- Upstream Check Logging (moved from routes.py) ---
def init_upstream_check_log():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS upstream_check_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT,
            upstream_name TEXT,
            check_url TEXT,
            result TEXT,
            detail TEXT,
            tried_at TEXT,
            count INTEGER DEFAULT 1,
            UNIQUE(pattern, upstream_name)
        )
    ''')
    # Add count column if missing (for upgrades)
    try:
        db.execute('ALTER TABLE upstream_check_log ADD COLUMN count INTEGER DEFAULT 1')
        db.commit()
    except Exception:
        pass
    db.commit()

def log_upstream_check(pattern, upstream_name, check_url, result, detail, tried_at):
    db = get_db()
    db.execute('''
        INSERT INTO upstream_check_log (pattern, upstream_name, check_url, result, detail, tried_at, count)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(pattern, upstream_name) DO UPDATE SET
            check_url=excluded.check_url,
            result=excluded.result,
            detail=excluded.detail,
            tried_at=excluded.tried_at,
            count=upstream_check_log.count+1
    ''', (pattern, upstream_name, check_url, result, detail, tried_at))
    db.commit()

def get_upstream_logs():
    db = get_db()
    cursor = db.execute('''
        SELECT pattern, upstream_name, check_url, result, detail, tried_at, count
        FROM upstream_check_log
        ORDER BY tried_at DESC, id DESC
        LIMIT 200
    ''')
    logs = []
    for row in cursor.fetchall():
        logs.append({
            'shortcut': row[0],
            'upstream': row[1],
            'check_url': row[2],
            'result': row[3],
            'details': row[4],
            'time': row[5],
            'count': row[6],
        })
    return logs

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
    _redis_host = redis_cfg.get('host', 'localhost')
    _redis_port = redis_cfg.get('port', 6379)
    if _redis_enabled:
        try:
            _redis_client = redis.Redis(host=_redis_host, port=_redis_port, decode_responses=True)
            _redis_client.ping()
            print(f"[INFO] Redis enabled: host={_redis_host}, port={_redis_port}")
        except Exception as e:
            print(f"[WARN] Redis config enabled but connection failed: {e}")
            _redis_enabled = False
    else:
        print("[INFO] Redis is disabled (see config)")

def redis_get(key):
    if _redis_enabled and _redis_client:
        try:
            return _redis_client.get(key)
        except Exception:
            return None
    return None

def redis_set(key, value):
    if _redis_enabled and _redis_client:
        try:
            _redis_client.set(key, value)
        except Exception:
            pass

def redis_delete(key):
    if _redis_enabled and _redis_client:
        try:
            _redis_client.delete(key)
        except Exception:
            pass

def get_shortcut(pattern):
    # Try Redis first
    shortcut = None
    if _redis_enabled:
        val = redis_get(f"shortcut:{pattern}")
        if val:
            try:
                shortcut = json.loads(val)
            except Exception:
                shortcut = None
    if shortcut:
        return shortcut
    # Fallback to DB
    db = get_db()
    cursor = db.execute('SELECT pattern, type, target, access_count, created_at, updated_at FROM redirects WHERE pattern=?', (pattern,))
    row = cursor.fetchone()
    if row:
        shortcut = dict(
            pattern=row[0],
            type=row[1],
            target=row[2],
            access_count=row[3] if row[3] is not None else 0,
            created_at=row[4],
            updated_at=row[5]
        )
        # Save to Redis for next time
        if _redis_enabled:
            try:
                redis_set(f"shortcut:{pattern}", json.dumps(shortcut))
            except Exception:
                pass
        return shortcut
    return None

def set_shortcut(pattern, type_, target, access_count=0, created_at=None, updated_at=None):
    db = get_db()
    now = updated_at or None
    cursor = db.execute('SELECT 1 FROM redirects WHERE pattern=?', (pattern,))
    exists = cursor.fetchone()
    if exists:
        db.execute('''
            UPDATE redirects
            SET type=?, target=?, updated_at=?
            WHERE pattern=?
        ''', (type_, target, now, pattern))
    else:
        db.execute('''
            INSERT INTO redirects (type, pattern, target, access_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (type_, pattern, target, access_count, created_at, now))
    db.commit()
    # Update Redis
    if _redis_enabled:
        shortcut = dict(
            pattern=pattern,
            type=type_,
            target=target,
            access_count=access_count,
            created_at=created_at,
            updated_at=now
        )
        try:
            redis_set(f"shortcut:{pattern}", json.dumps(shortcut))
        except Exception:
            pass

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
    print(ascii_art)
    print(f"==============================\n   GUNICORN MODE - READY\n==============================")
    print("URL Shortener & Redirector app initialized.")
    if app is not None:
        print(f"Configured to run on port: {app.config.get('port', 'unknown')}")
    else:
        print("(Port unknown: app not provided)")
    # Detect OS and print instructions for host file entry
    os_name = platform.system().lower()
    if os_name == "windows":
        print("\n==============================")
        print(f"Detected OS: Windows")
        print("==============================\n")
        print("Run the following command in PowerShell as Administrator:")
        print("  .\\scripts\\add-r-host-windows.ps1")
        print("Or manually add this line to C:\\Windows\\System32\\drivers\\etc\\hosts:")
        print("  127.0.0.1   r\n")
    elif os_name == "darwin":
        print("\n==============================")
        print(f"Detected OS: macOS")
        print("==============================\n")
        print("Run the following command in Terminal:")
        print("  bash scripts/add-r-host-macos.sh")
        print("Or manually edit /etc/hosts using:")
        print("  sudo nano /etc/hosts")
        print("Then add this line:")
        print("  127.0.0.1   r\n")
        print("Run `dscacheutil -flushcache && sudo killall -HUP mDNSResponder` to apply changes.\n")
    elif os_name == "linux":
        print("\n==============================")
        print(f"Detected OS: Linux")
        print("==============================\n")
        print("Run the following command in Terminal:")
        print("  bash scripts/add-r-host-linux.sh")
        print("Or manually edit /etc/hosts using:")
        print("  sudo nano /etc/hosts")
        print("Then add this line:")
        print("  127.0.0.1   r\n")
    else:
        print("Your OS is not explicitly supported. Please manually update your hosts file:\n")
        print("  127.0.0.1   r")
    # Print Redis status
    if _redis_enabled:
        print(f"[INFO] Redis enabled: host={_redis_host}, port={_redis_port}")
    else:
        print("[INFO] Redis is disabled (see config)")

    # Check if 'r' hostname resolves to localhost
    import socket
    try:
        r_ip = socket.gethostbyname('r')
        if r_ip == '127.0.0.1':
            print("[INFO] Hostname 'r' resolves to 127.0.0.1 (OK)")
        else:
            print(f"[WARN] Hostname 'r' resolves to {r_ip} (not 127.0.0.1). Check your hosts/DNS setup.")
    except Exception:
        print("[WARN] Hostname 'r' does not resolve. Add '127.0.0.1   r' to your hosts file or set up DNS.")

    # Docker environment and port/network info
    import os
    running_in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')
    if running_in_docker:
        print("[INFO] Running inside a Docker container.")
        print("      The app listens on the internal container port (default 80).\n      To access externally, ensure you map the container port to a host port using '-p <host_port>:80' in Docker.")
        print("      If using Docker Compose or custom networks, check your port mappings and network mode.")
    else:
        print("[INFO] Not running in Docker. If using Docker, make sure to map ports correctly.")
