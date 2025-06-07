import io
import json
import logging  # Import logging
import os
import re
import time
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Blueprint, render_template, request, redirect, stream_with_context, url_for, session, jsonify, \
    send_file, Response
from flask import session as flask_session

from app import CONSTANTS
from model.redirect import Redirect  # Import Redirect model for export/import
from model.upstream_check_log import UpstreamCheckLog  # For clearing upstream logs
import app.utils as utils

# Get a logger instance for this module
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.context_processor
def inject_now():
    # Try to get version string (same logic as version page)
    try:
        import subprocess
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip()
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
        version = f"v1.{commit_count}.{commit_hash}"
    except Exception as e:
        version = 'unknown'
        logger.debug(f"Could not determine version from git: {e}")

    # Add redis_connected context (already relies on _redis_enabled from utils)
    redis_connected = bool(utils._redis_enabled)  # _redis_enabled is now a global var from utils

    # --- FIX: Use datetime.now(timezone.utc) ---
    return {'now': lambda: datetime.now(timezone.utc), 'version': version, 'redis_connected': redis_connected,
            'constants': CONSTANTS}


# These config functions are mostly for internal use, can be kept for consistency but main config is in utils
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'redirect.config.json')

def get_upstreams():
    cfg = utils._load_config()
    return cfg.get('upstreams', [])


def set_upstreams(upstreams):
    cfg = utils._load_config()
    cfg['upstreams'] = upstreams
    utils._save_config(cfg)

# --- Simple Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            logger.warning(f"Authentication required for {request.path}. User not logged in.")
            # If AJAX/JSON request, return JSON error
            if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            # Otherwise, redirect to login page
            return redirect(url_for('main.admin_login', next=request.path))
        logger.debug(f"User authenticated for {request.path}.")
        return f(*args, **kwargs)

    return decorated_function


# GET/POST: Admin login page and handler. Triggered when user visits /admin-login or submits login form.
@bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        admin_pwd = utils.get_admin_password()
        if request.form.get('password') == admin_pwd:
            session['admin_logged_in'] = True
            next_url = request.args.get('next') or url_for('main.dashboard')
            logger.info("Admin user logged in successfully.")
            return redirect(next_url)
        else:
            error = 'Invalid password.'
            logger.warning("Failed admin login attempt (invalid password).")
    return render_template('admin_login.html', error=error)


# GET: Logout endpoint. Triggered when user visits /logout.
@bp.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    logger.info("Admin user logged out.")
    return redirect(url_for('main.dashboard'))

# GET: Dashboard page. Triggered when user visits the root URL '/'.
@bp.route('/', methods=['GET'])
def dashboard():
    # Get the latest 5 updated shortcuts
    try:
        latest_shortcuts = Redirect.query.order_by(Redirect.updated_at.desc()).limit(5).all()
        # You might want to convert these SQLAlchemy objects to dictionaries if your
        # template expects simpler data, but often Jinja can handle direct object access.
        # Example for conversion (optional, if needed):
        # formatted_shortcuts = []
        # for s in latest_shortcuts:
        #     formatted_shortcuts.append({
        #         'pattern': s.pattern,
        #         'target': s.target,
        #         'access_count': s.access_count,
        #         'updated_at': s.updated_at
        #     })
        # logger.debug(f"Retrieved {len(formatted_shortcuts)} latest shortcuts for dashboard.")

        logger.debug(f"Retrieved {len(latest_shortcuts)} latest shortcuts for dashboard.")
    except Exception as e:
        logger.exception("Failed to retrieve latest shortcuts for dashboard.")
        latest_shortcuts = []  # Ensure an empty list if there's an error
    return render_template('dashboard.html', shortcuts=latest_shortcuts)





@bp.route('/delete/<path:subpath>', methods=['GET', 'POST'])
@login_required
def dashboard_delete(subpath):
    if utils.get_delete_requires_password():
        if request.method == 'POST':
            admin_pwd = utils.get_admin_password()
            if request.form.get('password') == admin_pwd:
                utils.deleteShortCut(subpath)
                logger.info(f"Shortcut '{subpath}' deleted by admin.")
                return redirect(url_for('main.dashboard'))
            else:
                error = 'Invalid password.'
                logger.warning(f"Failed delete attempt for '{subpath}' (invalid password).")
                return render_template('delete_confirm.html', error=error, subpath=subpath)
        else:
            logger.debug(f"Displaying delete confirmation for '{subpath}'.")
            return render_template('delete_confirm.html', subpath=subpath, error=None)
    else:
        logger.info(f"Shortcut '{subpath}' deleted (password not required).")
        utils.deleteShortCut(subpath)
        return redirect(url_for('main.dashboard'))


# GET/POST: Edit or create shortcut. Triggered when user visits /edit/<subpath> or submits edit form.
@bp.route('/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):

    shortcut, source_data, resp_time = utils.get_shortcut(subpath)

    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        current_time = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
        ip_address = request.remote_addr or 'unknown'

        try:
            utils.set_shortcut(
                pattern=subpath,
                type_=type_,
                target=target,
                created_at=current_time if not shortcut else None,
                updated_at=current_time,
                created_ip=ip_address if not shortcut else None,
                updated_ip=ip_address
            )
            logger.info(f"Shortcut '{subpath}' {'updated' if shortcut else 'created'}.")
            return render_template('success_create.html', pattern=subpath, target=target)
        except Exception as e:
            logger.exception(f"Failed to {'update' if shortcut else 'create'} shortcut '{subpath}'.")
            # You might want a different error template or message here
            return render_template('error.html', message=f"Failed to save shortcut: {e}")
    else:  # GET request
        if not shortcut:
            logger.debug(f"Displaying create shortcut page for new pattern: '{subpath}'.")
            return render_template('create_shortcut.html', pattern=subpath)
        logger.debug(f"Displaying edit shortcut page for existing pattern: '{subpath}'.")
        return render_template('edit_shortcut.html', pattern=subpath, type=shortcut['type'], target=shortcut['target'])


@bp.route('/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    logger.info(f"Attempting to handle redirect for subpath: '{subpath}'")
    # sanitize  pattern
    pattern,dynamicProp= utils.destructureSubPath(subpath)
    shortcut, data_source, resp_time = utils.get_shortcut(pattern)
    print(shortcut,data_source,resp_time)
    if shortcut:
        if (data_source == CONSTANTS.data_source_redirect or data_source == CONSTANTS.data_source_redis) and \
                shortcut.get(CONSTANTS.KEY_DATA_TYPE) == CONSTANTS.DATA_TYPE_STATIC:
            utils.increment_access_count(subpath)
            logger.info(
                f"Redirecting static shortcut: '{subpath}' -> '{shortcut['target']}' (Source: {data_source}, Time: {resp_time:.4f}s)")
            if utils.get_auto_redirect_delay() > 0:
                return render_template('redirect.html', target=shortcut['target'], delay=utils.get_auto_redirect_delay(), source=data_source, response_time=resp_time)
            return redirect(shortcut['target'], code=302)

        # UPSTREAM _HANDLING :::
        if data_source == CONSTANTS.data_source_upstream and shortcut.get('resolved_url'):
            logger.info(
                f"Redirecting upstream shortcut: '{subpath}' -> '{shortcut['resolved_url']}' (Source: {data_source}, Time: {resp_time:.4f}s)")
            if utils.get_auto_redirect_delay() > 0:
                return render_template('redirect.html', target=shortcut['resolved_url'],
                                       delay=utils.get_auto_redirect_delay(), source=data_source,
                                       response_time=resp_time)
            return redirect(shortcut['resolved_url'], code=302)

        if (data_source == CONSTANTS.data_source_redirect or data_source == CONSTANTS.data_source_redis) and \
                shortcut.get(CONSTANTS.KEY_DATA_TYPE) == CONSTANTS.DATA_TYPE_DYNAMIC:
            target=shortcut['target']

            if subpath == pattern:
                example_var = 'yourvalue'
                example_target = utils.replacePlaceHolders(target, example_var)
                logger.info(f"Dynamic shortcut '{pattern}' accessed without variable. Showing usage instructions.")
                return render_template('dynamic_shortcut_usage.html', pattern=pattern, var_name=utils.get_placeholder_vars(target)[0],
                                       example_target=example_target)
            if subpath.startswith(pattern + "/"):
                variable = subpath[len(pattern) + 1:]
                dest_url = re.sub(r"\{\w+\}", variable, target)
                utils.increment_access_count(pattern)
                logger.info(f"Redirecting dynamic shortcut: '{subpath}' -> '{dest_url}' (Source: {data_source})")
                if utils.get_auto_redirect_delay() > 0:
                    return render_template('redirect.html', target=dest_url, delay=utils.get_auto_redirect_delay(), source=data_source)
                return redirect(dest_url, code=302)

    logger.info(f"No direct shortcut found for '{subpath}'. Checking live upstreams.")
    if get_upstreams():
        first_segment = subpath.split('/')[0]
        logger.debug(f"Redirecting to upstream check UI for first segment: '{first_segment}'")
        return redirect(url_for('main.check_upstreams_ui', pattern=first_segment), code=302)

    logger.info(f"No upstreams configured. Redirecting to create shortcut page for '{subpath}'.")
    return redirect(url_for('main.edit_redirect', subpath=subpath))


# GET: Tutorial/help page. Triggered when user visits /tutorial.
@bp.route('/tutorial', methods=['GET'])
def tutorial():
    logger.debug("Rendering tutorial page.")
    return render_template('tutorial.html')


# --- Upstreams Config API ---
@bp.route('/admin/upstreams', methods=['GET', 'POST'])
@login_required
def admin_upstreams():
    error = None
    upstreams = get_upstreams()
    if request.method == 'POST':
        if 'delete' in request.form:
            idx = int(request.form['delete'])
            if 0 <= idx < len(upstreams):
                deleted_name = upstreams[idx].get('name', 'Unnamed Upstream')
                del upstreams[idx]
                set_upstreams(upstreams)
                logger.info(f"Deleted upstream: '{deleted_name}'")
                return redirect(url_for('main.admin_upstreams'))
            else:
                logger.warning(f"Attempted to delete non-existent upstream index: {idx}")
        else:
            new_upstreams = []
            i = 0
            while True:
                name = request.form.get(f'name_{i}')
                base_url = request.form.get(f'base_url_{i}')
                fail_url = request.form.get(f'fail_url_{i}')
                fail_status_code = request.form.get(f'fail_status_code_{i}')
                verify_ssl = request.form.get(f'verify_ssl_{i}') == 'on'

                if name is None and base_url is None and fail_url is None and fail_status_code is None:
                    break
                if name or base_url or fail_url:
                    try:
                        fail_status_code = int(fail_status_code) if fail_status_code else None
                    except ValueError:
                        fail_status_code = None
                        logger.warning(
                            f"Invalid fail_status_code for upstream '{name}': '{request.form.get(f'fail_status_code_{i}')}'. Setting to None.")
                    new_upstreams.append({
                        'name': name or '',
                        'base_url': base_url or '',
                        'fail_url': fail_url or '',
                        'fail_status_code': fail_status_code,
                        'verify_ssl': verify_ssl
                    })
                i += 1
            set_upstreams(new_upstreams)
            logger.info("Upstream configuration updated.")
            upstreams = new_upstreams  # Refresh the list for rendering
    logger.debug("Rendering admin upstreams page.")
    return render_template('admin_upstreams.html', upstreams=upstreams, error=error)


@bp.route('/check-upstreams-ui/<path:pattern>')  # Use path converter
def check_upstreams_ui(pattern):
    delay = get_auto_redirect_delay()
    logger.info(f"Displaying upstream check UI for pattern: '{pattern}', delay: {delay}s")
    return render_template('check_upstreams_stream.html', pattern=pattern, delay=delay)


@bp.route('/stream/check-upstreams/<path:pattern>')  # Use path converter
def stream_check_upstreams(pattern):
    @stream_with_context
    def event_stream():
        found = False
        redirect_url = None

        def send_log(message, extra_data=None):
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            data = {'log': f"[{timestamp}] {message}"}
            if extra_data:
                data.update(extra_data)
            yield f"data: {json.dumps(data)}\n\n"

        yield from send_log(f"🔍 Starting upstream check for pattern: `{pattern}`")
        logger.info(f"Stream initiated for upstream check of pattern: '{pattern}'")

        for up in get_upstreams():
            up_name = up.get('name', '[unnamed]')
            base_url = up.get('base_url', '').rstrip('/')
            fail_url = up.get('fail_url', '')  # Keep as is, rstrip is not desired for comparison here
            fail_status_code = str(up.get('fail_status_code')) if up.get('fail_status_code') else None
            verify_ssl = up.get('verify_ssl', False)

            # Basic validation of upstream config for current check
            if not base_url:
                yield from send_log(f"⚠️ Warning: Upstream '{up_name}' has no base_url configured. Skipping.")
                logger.warning(f"Upstream '{up_name}' missing base_url, skipping check.")
                continue
            if not fail_url:
                yield from send_log(
                    f"⚠️ Warning: Upstream '{up_name}' missing fail_url. This might lead to incorrect detections.")
                logger.warning(f"Upstream '{up_name}' missing fail_url.")

            check_url = f"{base_url}/{pattern}"
            yield from send_log(f"🌐 Checking upstream: {up_name}")
            yield from send_log(f"Constructed URL: {check_url}")
            yield from send_log(f"Fail criteria → URL: '{fail_url}', Status: {fail_status_code or 'Not specified'}")
            yield from send_log(f"SSL Verification: {'Enabled' if verify_ssl else 'Disabled'}")

            tried_at = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            try:
                resp = requests.get(check_url, allow_redirects=True, timeout=5, verify=verify_ssl)
                actual_url = resp.url
                status_code = str(resp.status_code)

                yield from send_log(f"➡️ Response received from {check_url} → {actual_url} (status {status_code})")
                logger.debug(f"Upstream '{up_name}' response: actual_url='{actual_url}', status='{status_code}'")

                fail_url_match = actual_url.startswith(fail_url) if fail_url else False
                fail_status_match = (fail_status_code is not None and status_code == fail_status_code)

                if not fail_url_match and (fail_status_code is None or not fail_status_match):
                    found = True
                    redirect_url = actual_url
                    utils.log_upstream_check(
                        pattern, up_name, check_url, 'success',
                        f"actual_url={actual_url}, status_code={status_code}", tried_at
                    )
                    if utils.is_upstream_cache_enabled():
                        utils.cache_upstream_result(pattern, up_name, actual_url, tried_at)
                    yield from send_log(
                        f"✅ Shortcut found in {up_name} (redirected to {actual_url}, status {status_code})",
                        {'found': True, 'redirect_url': redirect_url}
                    )
                    logger.info(f"Shortcut '{pattern}' successfully found in upstream '{up_name}'.")
                    break
                else:
                    utils.log_upstream_check(
                        pattern, up_name, check_url, 'fail',
                        f"actual_url={actual_url}, status_code={status_code}, fail_url_match={fail_url_match}, fail_status_match={fail_status_match}",
                        tried_at
                    )
                    yield from send_log(f"❌ Shortcut not found in {up_name} — matched fail criteria.")
                    logger.info(f"Shortcut '{pattern}' not found in upstream '{up_name}' (matched fail criteria).")

            except requests.exceptions.Timeout:
                utils.log_upstream_check(pattern, up_name, check_url, 'timeout', 'Request timed out', tried_at)
                yield from send_log(f"⚠️ Timeout checking {up_name}: Request timed out after 5 seconds.",
                                    {'error': True})
                logger.error(f"Upstream check for '{up_name}' timed out for pattern '{pattern}'.")
            except requests.exceptions.ConnectionError as e:
                utils.log_upstream_check(pattern, up_name, check_url, 'connection_error', str(e), tried_at)
                yield from send_log(f"⚠️ Connection error checking {up_name}: {str(e)}", {'error': True})
                logger.error(f"Connection error for upstream '{up_name}' and pattern '{pattern}': {e}")
            except requests.exceptions.RequestException as e:
                utils.log_upstream_check(pattern, up_name, check_url, 'request_exception', str(e), tried_at)
                yield from send_log(f"⚠️ HTTP request error for {up_name}: {str(e)}", {'error': True})
                logger.error(f"HTTP request error for upstream '{up_name}' and pattern '{pattern}': {e}")
            except Exception as e:
                utils.log_upstream_check(pattern, up_name, check_url, 'exception', str(e), tried_at)
                yield from send_log(f"⚠️ An unexpected error occurred for {up_name}: {str(e)}", {'error': True})
                logger.exception(f"Unexpected error during upstream check for '{up_name}' and pattern '{pattern}'.")

            yield from send_log(f"--- Finished check for {up_name} ---")
            time.sleep(0.5)

        if not found:
            yield from send_log("🔚 No upstream found containing the shortcut.")
            logger.info(f"No upstream found for pattern: '{pattern}'.")
            yield f"data: {json.dumps({'done': True})}\n\n"
        else:
            yield f"data: {json.dumps({'done': True, 'final_redirect_url': redirect_url})}\n\n"  # Send final redirect for client-side action

    return Response(event_stream(), mimetype='text/event-stream')


@bp.route('/admin/upstream-logs')
@login_required
def admin_upstream_logs():
    logs = get_upstream_logs()
    cache_status_map = {}
    if is_upstream_cache_enabled():
        for up in get_upstreams():
            cached = list_upstream_cache(up.get('name'))
            for entry in cached:
                cache_status_map[(entry['pattern'], up.get('name'))] = {'checked_at': entry['checked_at']}
    logger.debug("Rendering admin upstream logs page.")
    return render_template('admin_upstream_logs.html', logs=logs, cache_status_map=cache_status_map)


@bp.route('/admin/export-redirects')
@login_required
def admin_export_redirects():
    redirects = Redirect.query.all()
    exported_data = []
    for r in redirects:
        exported_data.append({
            'id': r.id,
            'pattern': r.pattern,
            'type': r.type,
            'target': r.target,
            'access_count': r.access_count,
            'created_at': r.created_at,
            'updated_at': r.updated_at,
            'created_ip': r.created_ip,
            'updated_ip': r.updated_ip
        })

    buf = io.BytesIO(json.dumps(exported_data, indent=2).encode('utf-8'))
    buf.seek(0)
    logger.info(f"Exported {len(exported_data)} redirects.")
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name='redirects.json')



@bp.route('/admin/import-redirects', methods=['GET', 'POST'])
@login_required
def admin_import_redirects():
    error = None
    success = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.json'):
            try:
                # Read file content first
                file_content = file.read()
                data = json.loads(file_content)

                # Call the utility function
                import_result = import_redirects_from_json(data)

                if import_result['success']:
                    success = import_result['message']
                    logger.info(f"Admin import operation successful: {success}")
                else:
                    error = import_result['message']
                    logger.error(f"Admin import operation failed: {error}")

            except json.JSONDecodeError as e:
                error = f'Import failed: Invalid JSON file content: {e}'
                logger.error(f"Import failed due to JSONDecodeError: {e}")
            except Exception as e:
                error = f'Import failed: An unexpected error occurred during file processing: {e}'
                logger.exception(f"Unexpected error during file processing for redirect import.")
        else:
            error = 'Please upload a valid .json file.'
            logger.warning("Import failed: No file or invalid file type uploaded.")

    logger.debug("Rendering admin import/export page.")
    return render_template('admin_import_export.html', error=error, success=success, session=flask_session)



@bp.route('/api/check-shortcut-exists/<path:pattern>')  # Use path converter
def api_check_shortcut_exists(pattern):
    exists = isPatternExists(pattern)
    logger.debug(f"API check for shortcut '{pattern}' exists: {exists}")
    return jsonify({'exists': exists})


@bp.route('/edit/', methods=['GET', 'POST'])
@login_required
def edit_redirect_blank():
    if request.method == 'POST':
        pattern = request.form.get('pattern', '').strip()
        type_ = request.form.get('type', CONSTANTS.DATA_TYPE_STATIC)
        target = request.form.get('target', '').strip()
        current_time = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        ip_address = request.remote_addr or 'unknown'

        if not pattern:
            logger.warning("Attempted to create shortcut with empty pattern.")
            return render_template('create_shortcut.html', pattern='', error='Shortcut pattern cannot be empty.')

        if isPatternExists(pattern):
            logger.warning(f"Attempted to create shortcut '{pattern}' which already exists.")
            return render_template('create_shortcut.html', pattern=pattern,
                                   error='A shortcut with this pattern already exists.')

        try:
            set_shortcut(
                pattern=pattern,
                type_=type_,
                target=target,
                created_at=current_time,
                updated_at=current_time,
                created_ip=ip_address,
                updated_ip=ip_address
            )
            logger.info(f"New shortcut '{pattern}' created successfully via blank edit route.")
            return render_template('success_create.html', pattern=pattern, target=target)
        except Exception as e:
            logger.exception(f"Failed to create new shortcut '{pattern}' via blank edit route.")
            return render_template('error.html', message=f"Failed to create shortcut: {e}")

    logger.debug("Rendering blank create shortcut page.")
    return render_template('create_shortcut.html', pattern='')


# GET: Instructions page for enabling r/ shortcuts
@bp.route('/enable-r-instructions', methods=['GET'])
def enable_r_instructions():
    logger.debug("Rendering enable r/ instructions page.")
    return render_template('enable_r_instructions.html')


# --- Upstream Cache Management ---
@bp.route('/admin/upstream-cache/<upstream>')
@login_required
def admin_upstream_cache(upstream):
    cached = list_upstream_cache(upstream)
    logger.debug(f"Rendering admin upstream cache page for '{upstream}'.")
    return render_template('admin_upstream_cache.html', upstream=upstream, cached=cached)


@bp.route('/admin/upstream-cache/resync/<upstream>/<path:pattern>', methods=['GET', 'POST'])
@login_required
def admin_upstream_cache_resync(upstream, pattern):
    try:
        logger.info(f"Admin initiated resync for upstream='{upstream}', pattern='{pattern}'")
        up = next((u for u in get_upstreams() if u.get('name') == upstream), None)
        if not up:
            logger.warning(f"Upstream '{upstream}' not found during resync operation.")
            return jsonify({'success': False, 'error': 'Upstream not found'}), 404

        base_url = up.get('base_url', '').rstrip('/')
        check_url = f"{base_url}/{pattern}"

        try:
            verify_ssl = up.get('verify_ssl', False)
            resp = requests.get(check_url, allow_redirects=True, timeout=5, verify=verify_ssl)
            actual_url = resp.url
            status_code = str(resp.status_code)

            fail_url = up.get('fail_url', '')
            fail_status_code = str(up.get('fail_status_code')) if up.get('fail_status_code') else None

            fail_url_match = actual_url.startswith(fail_url) if fail_url else False
            fail_status_match = (fail_status_code is not None and status_code == fail_status_code)

            logger.debug(
                f"Resync check for '{pattern}' in '{upstream}': actual_url='{actual_url}', status='{status_code}', fail_url_match={fail_url_match}, fail_status_match={fail_status_match}")

            if not fail_url_match and (fail_status_code is None or not fail_status_match):
                tried_at = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
                utils.cache_upstream_result(pattern, upstream, actual_url, tried_at)
                logger.info(f"Resync for '{pattern}' in '{upstream}' successful, cache updated.")
                return jsonify({'success': True, 'resolved_url': actual_url, 'checked_at': tried_at})
            else:
                clear_upstream_cache(pattern)
                logger.info(f"Resync for '{pattern}' in '{upstream}' failed (matched fail criteria), cache cleared.")
                return jsonify({'success': False, 'error': 'Pattern not found in upstream (fail criteria matched).',
                                'checked_at': datetime.utcnow().isoformat(sep=' ', timespec='seconds')})
        except requests.exceptions.RequestException as e:
            clear_upstream_cache(pattern)
            logger.error(f"Resync upstream check for '{pattern}' in '{upstream}' failed with HTTP error: {e}")
            return jsonify({'success': False, 'error': f"Upstream check failed: {str(e)}",
                            'checked_at': datetime.utcnow().isoformat(sep=' ', timespec='seconds')})
        except Exception as e:
            clear_upstream_cache(pattern)
            logger.exception(f"Unexpected error during resync upstream check for '{pattern}' in '{upstream}'.")
            return jsonify({'success': False, 'error': f"An unexpected error occurred during upstream check: {str(e)}",
                            'checked_at': datetime.utcnow().isoformat(sep=' ', timespec='seconds')})
    except Exception as e:
        logger.exception(f"Top-level error during admin_upstream_cache_resync for '{upstream}'.")
        return jsonify(
            {'success': False, 'error': 'Unexpected server error during resync operation', 'details': str(e)}), 500


@bp.route('/admin/upstream-cache/purge/<upstream>', methods=['POST'])
@login_required
def admin_upstream_cache_purge(upstream):
    try:
        cached_entries_for_upstream = list_upstream_cache(upstream)  # Get all entries for the upstream
        purged_count = 0
        for entry in cached_entries_for_upstream:
            clear_upstream_cache(entry['pattern'])  # clear_upstream_cache operates on a single pattern
            purged_count += 1
        logger.info(f"Purged {purged_count} cache entries for upstream: '{upstream}'.")
        return jsonify({'success': True, 'purged': purged_count})
    except Exception as e:
        logger.exception(f"Error purging cache for upstream: '{upstream}'.")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/admin/upstream-cache/resync-all/<upstream>', methods=['POST'])
@login_required
def admin_upstream_cache_resync_all(upstream):
    try:
        logger.info(f"Admin initiated full resync for all cached patterns in upstream: '{upstream}'.")
        up = next((u for u in get_upstreams() if u.get('name') == upstream), None)
        if not up:
            logger.warning(f"Upstream '{upstream}' not found during resync-all operation.")
            return jsonify({'success': False, 'error': 'Upstream not found'}), 404

        base_url = up.get('base_url', '').rstrip('/')
        fail_url = up.get('fail_url', '')
        fail_status_code = str(up.get('fail_status_code')) if up.get('fail_status_code') else None
        verify_ssl = up.get('verify_ssl', False)

        cached_entries_for_upstream = list_upstream_cache(upstream)
        patterns_to_check = [entry['pattern'] for entry in cached_entries_for_upstream]

        results = []
        for pattern in patterns_to_check:
            check_url = f"{base_url}/{pattern}"
            try:
                resp = requests.get(check_url, allow_redirects=True, timeout=5, verify=verify_ssl)
                actual_url = resp.url
                status_code = str(resp.status_code)

                fail_url_match = actual_url.startswith(fail_url) if fail_url else False
                fail_status_match = (fail_status_code is not None and status_code == fail_status_code)
                tried_at = datetime.utcnow().isoformat(sep=' ', timespec='seconds')

                if not fail_url_match and (fail_status_code is None or not fail_status_match):
                    utils.cache_upstream_result(pattern, upstream, actual_url, tried_at)
                    results.append(
                        {'pattern': pattern, 'success': True, 'resolved_url': actual_url, 'checked_at': tried_at})
                    logger.debug(f"Resync-all: Pattern '{pattern}' in '{upstream}' successful.")
                else:
                    clear_upstream_cache(pattern)
                    results.append({'pattern': pattern, 'success': False, 'error': 'Fail criteria matched',
                                    'checked_at': tried_at})
                    logger.debug(f"Resync-all: Pattern '{pattern}' in '{upstream}' failed (matched fail criteria).")
            except requests.exceptions.RequestException as e:
                clear_upstream_cache(pattern)
                results.append({'pattern': pattern, 'success': False, 'error': f"Upstream check failed: {str(e)}",
                                'checked_at': datetime.utcnow().isoformat(sep=' ', timespec='seconds')})
                logger.error(f"Resync-all: HTTP error for '{pattern}' in '{upstream}': {e}")
            except Exception as e:
                clear_upstream_cache(pattern)
                results.append(
                    {'pattern': pattern, 'success': False, 'error': f"An unexpected error occurred: {str(e)}",
                     'checked_at': datetime.utcnow().isoformat(sep=' ', timespec='seconds')})
                logger.exception(f"Resync-all: Unexpected error for '{pattern}' in '{upstream}'.")
        logger.info(f"Finished full resync for upstream: '{upstream}'. Processed {len(patterns_to_check)} patterns.")
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.exception(f"Top-level error during admin_upstream_cache_resync_all for '{upstream}'.")
        return jsonify(
            {'success': False, 'error': 'Unexpected server error during resync-all operation', 'details': str(e)}), 500


@bp.route('/admin/clear-upstream-logs', methods=['POST'])
@login_required
def clear_upstream_logs():
    from model import db  # Get db instance from model
    db.session.query(UpstreamCheckLog).delete()
    db.session.commit()
    logger.info("All upstream check logs cleared.")
    return redirect(url_for('main.admin_upstream_logs'))


# Global error handler for 500 errors: return JSON if requested
@bp.app_errorhandler(500)
def handle_500_error(e):
    logger.exception("An unhandled 500 error occurred.")  # Log the exception at ERROR level
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500