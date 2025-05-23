from flask import Blueprint, render_template, request, redirect, url_for, g, session, abort
import sqlite3, re
from .utils import get_db, get_admin_password, get_port, get_auto_redirect_delay, DASHBOARD_TEMPLATE, get_delete_requires_password, increment_access_count, get_access_count, get_created_updated
from functools import wraps
from datetime import datetime

bp = Blueprint('main', __name__)

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

# POST: Create new shortcut. Triggered when user submits the create shortcut form.
@bp.route('/create', methods=['POST'])
def dashboard_create():
    db = get_db()
    pattern = request.form['pattern']
    type_ = request.form['type']
    target = request.form['target']
    db.execute('INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)', (type_, pattern, target))
    db.commit()
    return redirect(url_for('main.dashboard'))

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

# GET/POST: Edit shortcut. Triggered when user visits /edit/<subpath> or submits edit form.
@bp.route('/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):
    db = get_db()
    from .utils import get_access_count, get_created_updated
    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        ip = request.remote_addr or ''
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
