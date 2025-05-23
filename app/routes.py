from flask import Blueprint, render_template, request, redirect, url_for, g, session, abort
import sqlite3, re
from .utils import get_db, get_admin_password, get_port, get_auto_redirect_delay, DASHBOARD_TEMPLATE, get_delete_requires_password, increment_access_count, get_access_count, get_created_updated
from functools import wraps
from datetime import datetime
import json
import os
import requests
from flask import jsonify

bp = Blueprint('main', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'redirect.json.config')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

def get_upstreams():
    cfg = load_config()
    return cfg.get('upstreams', [])

def set_upstreams(upstreams):
    cfg = load_config()
    cfg['upstreams'] = upstreams
    save_config(cfg)

# --- Simple Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return render_template('admin_login.html', error=None)
        return f(*args, **kwargs)
    return decorated_function

# GET/POST: Admin login page and handler. Triggered when user visits /admin-login or submits login form.
@bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        admin_pwd = get_admin_password()
        if request.form.get('password') == admin_pwd:
            session['admin_logged_in'] = True
            next_url = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_url)
        else:
            error = 'Invalid password.'
    return render_template('admin_login.html', error=error, now=datetime.utcnow)

# GET: Logout endpoint. Triggered when user visits /logout.
@bp.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.dashboard'))

# GET: Dashboard page. Triggered when user visits the root URL '/'.
@bp.route('/', methods=['GET'])
def dashboard():
    db = get_db()
    cursor = db.execute('SELECT pattern, type, target, access_count, created_at, updated_at FROM redirects ORDER BY pattern ASC')
    shortcuts = [
        dict(
            pattern=row[0],
            type=row[1],
            target=row[2],
            access_count=row[3] if row[3] is not None else 0,
            created_at=row[4],
            updated_at=row[5]
        ) for row in cursor.fetchall()
    ]
    return render_template('dashboard.html', shortcuts=shortcuts, now=datetime.utcnow)

# # POST: Create new shortcut. Triggered when user submits the create shortcut form.
# @bp.route('/create', methods=['POST'])
# def dashboard_create():
#     db = get_db()
#     pattern = request.form['pattern']
#     type_ = request.form['type']
#     target = request.form['target']
#     # --- Upstream check before creation ---
#     all_failed, logs = check_upstreams_for_shortcut(pattern)
#     for log in logs:
#         print(log)
#     if not all_failed:
#         return render_template('create_shortcut.html', pattern=pattern, now=datetime.utcnow, logs=logs, error='Shortcut exists in upstream!')
#     db.execute('INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)', (type_, pattern, target))
#     db.commit()
#     # On success, do not show logs
#     return render_template('success_create.html', pattern=pattern, target=target, now=datetime.utcnow)

# GET/POST: Delete shortcut. Triggered when user visits /delete/<subpath> or submits delete confirmation.
@bp.route('/delete/<path:subpath>', methods=['GET', 'POST'])
def dashboard_delete(subpath):
    db = get_db()
    if get_delete_requires_password():
        if request.method == 'POST':
            admin_pwd = get_admin_password()
            if request.form.get('password') == admin_pwd:
                db.execute('DELETE FROM redirects WHERE pattern=?', (subpath,))
                db.commit()
                return redirect(url_for('main.dashboard'))
            else:
                error = 'Invalid password.'
                return render_template('delete_confirm.html', error=error, now=datetime.utcnow)
        else:
            return render_template('delete_confirm_noerror.html', now=datetime.utcnow)
    else:
        db.execute('DELETE FROM redirects WHERE pattern=?', (subpath,))
        db.commit()
        return redirect(url_for('main.dashboard'))

# GET/POST: Edit or create shortcut. Triggered when user visits /edit/<subpath> or submits edit form.
@bp.route('/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):
    db = get_db()

    # --- Upstream check done during GET ---
    if request.method == 'GET':
        # Check upstreams before even allowing user to create
        all_failed, logs = check_upstreams_for_shortcut(subpath)
        if not all_failed:
            # Redirect to the first upstream match
            for log in logs:
                if "found existing shortcut at" in log:
                    match = re.search(r"redirected to (http[s]?://\S+)", log)
                    if match:
                        redirect_url = match.group(1)
                        return redirect(redirect_url, code=302)

        # Check if exists locally, if not prepare for creation
        cursor = db.execute('SELECT type, target FROM redirects WHERE pattern=?', (subpath,))
        row = cursor.fetchone()
        if not row:
            return render_template('create_shortcut.html', pattern=subpath, now=datetime.utcnow)
        return render_template('edit_shortcut.html', pattern=subpath, type=row[0], target=row[1], now=datetime.utcnow)

    # POST: Form was submitted to update/create shortcut
    elif request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        ip = request.remote_addr or ''

        # Proceed with insert/update (upstream was already checked on GET)
        cursor = db.execute('SELECT 1 FROM redirects WHERE pattern=?', (subpath,))
        exists = cursor.fetchone()

        if exists:
            db.execute('''
                UPDATE redirects
                SET type=?, target=?, updated_at=?, updated_ip=?
                WHERE pattern=?
            ''', (type_, target, now, ip, subpath))
        else:
            db.execute('''
                INSERT INTO redirects
                (type, pattern, target, created_at, updated_at, created_ip, updated_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (type_, subpath, target, now, now, ip, ip))
        db.commit()

        return render_template('success_create.html', pattern=subpath, target=target, now=datetime.utcnow)

    db = get_db()
    from .utils import get_access_count, get_created_updated
    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        ip = request.remote_addr or ''
        # --- Upstream check before edit/creation ---
        all_failed, logs = check_upstreams_for_shortcut(subpath)
        for log in logs:
            print(log)
        if not all_failed:
            # Show error and logs if shortcut exists in upstream
            return render_template('edit_shortcut.html', pattern=subpath, type=type_, target=target, now=datetime.utcnow, logs=logs, error='Shortcut exists in upstream!')
        cursor = db.execute('SELECT 1 FROM redirects WHERE pattern=?', (subpath,))
        exists = cursor.fetchone()
        if exists:
            db.execute('UPDATE redirects SET type=?, target=?, updated_at=?, updated_ip=? WHERE pattern=?', (type_, target, now, ip, subpath))
            db.commit()
            return render_template('success_create.html', pattern=subpath, target=target, now=datetime.utcnow)
        else:
            db.execute('INSERT INTO redirects (type, pattern, target, created_at, updated_at, created_ip, updated_ip) VALUES (?, ?, ?, ?, ?, ?, ?)', (type_, subpath, target, now, now, ip, ip))
            db.commit()
            return render_template('success_create.html', pattern=subpath, target=target, now=datetime.utcnow)
    else:
        cursor = db.execute('SELECT type, target FROM redirects WHERE pattern=?', (subpath,))
        row = cursor.fetchone()
        if not row:
            return render_template('create_shortcut.html', pattern=subpath, now=datetime.utcnow)
        return render_template('edit_shortcut.html', pattern=subpath, type=row[0], target=row[1], now=datetime.utcnow)

# GET: Handle redirect for static and dynamic shortcuts. Triggered for any /<subpath> not matching other routes.
@bp.route('/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    db = get_db()
    cursor = db.execute('SELECT target FROM redirects WHERE type = ? AND pattern = ?', ('static', subpath))
    row = cursor.fetchone()
    if row:
        increment_access_count(subpath)
        if get_auto_redirect_delay() > 0:
            return render_template('redirect.html', target=row[0], delay=get_auto_redirect_delay(), now=datetime.utcnow)
        return redirect(row[0], code=302)
    # Check if subpath matches a dynamic pattern but is missing the variable
    cursor = db.execute('SELECT pattern, target FROM redirects WHERE type = ?', ('dynamic',))
    for pattern, target in cursor.fetchall():
        import re as _re
        match = _re.search(r'\{(\w+)\}', target)
        var_name = match.group(1) if match else 'name'
        if subpath == pattern:
            example_var = 'yourvalue'
            example_url = f'/{pattern}/' + example_var
            example_target = target.replace(f'{{{var_name}}}', example_var)
            return render_template('dynamic_shortcut_usage.html', pattern=pattern, var_name=var_name, example_target=example_target, now=datetime.utcnow)
        if subpath.startswith(pattern + "/"):
            variable = subpath[len(pattern)+1:]
            dest_url = _re.sub(r"\{\w+\}", variable, target)
            increment_access_count(pattern)
            if get_auto_redirect_delay() > 0:
                return render_template('redirect.html', target=dest_url, delay=get_auto_redirect_delay(), now=datetime.utcnow)
            return redirect(dest_url, code=302)
    return redirect(url_for('main.edit_redirect', subpath=subpath), code=302)

# GET: Tutorial/help page. Triggered when user visits /tutorial.
@bp.route('/tutorial', methods=['GET'])
def tutorial():
    return render_template('tutorial.html', now=datetime.utcnow)

# --- Upstreams Config API ---
@bp.route('/admin/upstreams', methods=['GET', 'POST'])
@login_required
def admin_upstreams():
    error = None
    upstreams = get_upstreams()
    if request.method == 'POST':
        # Handle delete
        if 'delete' in request.form:
            idx = int(request.form['delete'])
            if 0 <= idx < len(upstreams):
                del upstreams[idx]
                set_upstreams(upstreams)
                return redirect(url_for('main.admin_upstreams'))
        # Handle save (add/edit)
        else:
            # Rebuild upstreams from form
            new_upstreams = []
            i = 0
            while True:
                name = request.form.get(f'name_{i}')
                base_url = request.form.get(f'base_url_{i}')
                fail_url = request.form.get(f'fail_url_{i}')
                fail_status_code = request.form.get(f'fail_status_code_{i}')
                if name is None and base_url is None and fail_url is None and fail_status_code is None:
                    break
                if name or base_url or fail_url:
                    try:
                        fail_status_code = int(fail_status_code) if fail_status_code else None
                    except Exception:
                        fail_status_code = None
                    new_upstreams.append({
                        'name': name or '',
                        'base_url': base_url or '',
                        'fail_url': fail_url or '',
                        'fail_status_code': fail_status_code
                    })
                i += 1
            set_upstreams(new_upstreams)
            upstreams = new_upstreams
    return render_template('admin_upstreams.html', upstreams=upstreams, error=error)

# --- Upstream Shortcut Existence Check ---
def check_upstreams_for_shortcut(shortcut):
    logs = []
    all_failed = True
    for up in get_upstreams():
        check_url = up['base_url'].rstrip('/') + '/' + shortcut
        fail_url = up['fail_url']
        fail_status_code = up.get('fail_status_code')
        try:
            resp = requests.get(check_url, allow_redirects=True, timeout=3)
            logs.append(f"Checking {up['name']}: {check_url} → {resp.url} (status {resp.status_code})")
            # If the final URL is not the fail_url, or status code is not the fail_status_code, shortcut exists
            fail_url_match = resp.url.rstrip('/') == fail_url.rstrip('/')
            fail_status_match = str(resp.status_code) == str(fail_status_code) if fail_status_code is not None else False
            if not fail_url_match or (fail_status_code is not None and not fail_status_match):
                all_failed = False
                logs.append(f"{up['name']} found existing shortcut at {check_url} (redirected to {resp.url}, status {resp.status_code})")
            else:
                logs.append(f"{up['name']} did not find shortcut (landed on fail_url/status)")
        except Exception as e:
            logs.append(f"{up['name']} check failed: {str(e)}")
    return all_failed, logs

@bp.route('/check-upstreams/<pattern>', methods=['GET'])
def check_upstreams_page(pattern):
    return render_template('check_upstreams.html', pattern=pattern)

@bp.route('/api/check-upstreams/<pattern>', methods=['GET'])
def api_check_upstreams(pattern):
    logs = []
    found = False
    redirect_url = None
    for up in get_upstreams():
        check_url = up['base_url'].rstrip('/') + '/' + pattern
        fail_url = up['fail_url']
        fail_status_code = up.get('fail_status_code')
        try:
            resp = requests.get(check_url, allow_redirects=True, timeout=3)
            logs.append(f"Checking {up['name']}: {check_url} → {resp.url} (status {resp.status_code})")
            fail_url_match = resp.url.rstrip('/') == fail_url.rstrip('/')
            fail_status_match = str(resp.status_code) == str(fail_status_code) if fail_status_code is not None else False
            if not fail_url_match or (fail_status_code is not None and not fail_status_match):
                found = True
                redirect_url = resp.url
                logs.append(f"{up['name']} found existing shortcut at {check_url} (redirected to {resp.url}, status {resp.status_code})")
                break
            else:
                logs.append(f"{up['name']} did not find shortcut (landed on fail_url/status)")
        except Exception as e:
            logs.append(f"{up['name']} check failed: {str(e)}")
    return jsonify({'found': found, 'logs': logs, 'redirect_url': redirect_url})
