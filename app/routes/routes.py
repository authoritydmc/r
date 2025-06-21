import io
import json
import logging  # Import logging
from datetime import datetime
import os

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, \
    send_file, flash
from flask import session as flask_session

from app.routes.routesUtils import login_required
from app.utils import utils
from model.redirect import Redirect  # Import Redirect model for export/import

# Get a logger instance for this module
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

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
    try:
        count = int(request.args.get('count', 5))
        sort = request.args.get('sort', 'updated')
        if sort == 'created':
            latest_shortcuts = Redirect.query.order_by(Redirect.created_at.desc()).limit(count).all()
        else:
            latest_shortcuts = Redirect.query.order_by(Redirect.updated_at.desc()).limit(count).all()
        logger.debug(f"Retrieved {len(latest_shortcuts)} latest shortcuts for dashboard.")
    except Exception as e:
        logger.exception("Failed to retrieve latest shortcuts for dashboard.")
        latest_shortcuts = []
    # r/ hostname detection logic
    r_hostname_enabled = False
    # Check config file for r/ hostname
    try:
        from app.utils.utils import get_config
        hostnames = []
        config_val = get_config('hostnames', None)
        if config_val:
            if isinstance(config_val, list):
                hostnames = config_val
            elif isinstance(config_val, str):
                hostnames = [config_val]
        # Also check environment variable if set
        env_host = os.environ.get('HOSTNAME')
        if env_host:
            hostnames.append(env_host)
        for h in hostnames:
            if h.lower().startswith('r.') or h.lower().startswith('r/'):
                r_hostname_enabled = True
                break
    except Exception:
        pass
    return render_template('dashboard.html', shortcuts=latest_shortcuts, count=count, sort=sort, r_hostname_enabled=r_hostname_enabled)




# GET: Tutorial/help page. Triggered when user visits /tutorial.
@bp.route('/tutorial', methods=['GET'])
def tutorial():
    logger.debug("Rendering tutorial page.")
    return render_template('tutorial.html')



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
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    filename = f'redirects-{timestamp}.json'
    logger.info(f"Exported {len(exported_data)} redirects to {filename}.")
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name=filename)



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
                import_result = utils.import_redirects_from_json(data)

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
    exists = utils.isPatternExists(pattern)
    logger.debug(f"API check for shortcut '{pattern}' exists: {exists}")
    return jsonify({'exists': exists})

# GET: Instructions page for enabling r/ shortcuts
@bp.route('/enable-r-instructions', methods=['GET'])
def enable_r_instructions():
    logger.debug("Rendering enable r/ instructions page.")
    return render_template('enable_r_instructions.html')


# Admin: View and delete Redis cache entries
@bp.route('/admin/redis-cache', methods=['GET'])
@login_required
def admin_redis_cache():
    redis_keys = []
    redis_values = {}
    error = None
    if utils.config.redis_enabled and utils.config.redis_client:
        try:
            redis_keys = utils.config.redis_client.keys('*')
            for k in redis_keys:
                try:
                    redis_values[k] = utils.config.redis_client.get(k)
                except Exception:
                    redis_values[k] = '[Error reading value]'
        except Exception as e:
            error = str(e)
    return render_template('admin_redis_cache.html', redis_keys=redis_keys, redis_values=redis_values, error=error)

@bp.route('/admin/redis-cache/delete', methods=['POST'])
@login_required
def admin_redis_cache_delete():
    key = request.form.get('key')
    if not key:
        return jsonify({'success': False, 'error': 'No key provided'}), 400
    try:
        if utils.config.redis_enabled and utils.config.redis_client:
            if key == '*':
                keys = utils.config.redis_client.keys('*')
                if keys:
                    utils.config.redis_client.delete(*keys)
            else:
                utils.config.redis_client.delete(key)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Redis not enabled'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Dashboard: Dynamic shortcut count selection
@bp.route('/dashboard-shortcuts', methods=['GET'])
def dashboard_shortcuts():
    try:
        count = int(request.args.get('count', 5))
        sort = request.args.get('sort', 'updated')
        if sort == 'created':
            shortcuts = Redirect.query.order_by(Redirect.created_at.desc()).limit(count).all()
        else:
            shortcuts = Redirect.query.order_by(Redirect.updated_at.desc()).limit(count).all()
        result = []
        for s in shortcuts:
            result.append({
                'pattern': s.pattern,
                'type': s.type,
                'target': s.target,
                'access_count': s.access_count,
                'created_at': s.created_at,
                'updated_at': s.updated_at
            })
        return jsonify({'success': True, 'shortcuts': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/delete-shortcut/<pattern>', methods=['POST'])
@login_required
def api_delete_shortcut(pattern):
    try:
        shortcut = Redirect.query.filter_by(pattern=pattern).first()
        if not shortcut:
            return jsonify({'success': False, 'error': 'Shortcut not found'}), 404
        utils.db.session.delete(shortcut)
        utils.db.session.commit()
        # Clear Redis cache for this shortcut if enabled
        try:
            if utils.config.redis_enabled and utils.config.redis_client:
                redis_key = f"shortcut:{pattern}"
                utils.config.redis_client.delete(redis_key)
                logger.info(f"Cleared Redis cache for shortcut '{pattern}' after deletion.")
        except Exception as e:
            logger.warning(f"Failed to clear Redis cache for shortcut '{pattern}': {e}")
        logger.info(f"Shortcut '{pattern}' deleted by admin.")
        return jsonify({'success': True})
    except Exception as e:
        logger.exception(f"Failed to delete shortcut '{pattern}'")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    from app.config import get_config_data, save_config_data
    config_data = get_config_data()
    if request.method == 'POST':
        try:
            # Only update allowed fields
            form_data = request.form.to_dict()
            # Optionally: filter/validate fields here
            save_config_data(form_data)
            flash('Configuration updated successfully.', 'success')
            config_data = get_config_data()  # Reload after save
        except Exception as e:
            flash(f'Failed to update configuration: {e}', 'error')
    return render_template('admin_config.html', config_data=config_data)
