from flask import Blueprint, render_template_string, request, redirect, url_for, g, session, abort
import sqlite3, re
from .utils import get_db, get_admin_password, get_port, get_auto_redirect_delay, DASHBOARD_TEMPLATE
from functools import wraps

bp = Blueprint('main', __name__)

# --- Simple Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return render_template_string('''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 min-h-screen flex items-center justify-center"><div class="bg-white rounded-lg shadow p-8 w-full max-w-sm"><h2 class="text-2xl font-bold mb-4 text-blue-700">Admin Login</h2><form method="post" class="space-y-4"><input type="password" name="password" class="border rounded px-3 py-2 w-full" placeholder="Admin Password" required><button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full" type="submit">Login</button></form>{% if error %}<div class="text-red-600 mt-2">{{ error }}</div>{% endif %}</div></body></html>''', error=None)
        return f(*args, **kwargs)
    return decorated_function

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
    return render_template_string('''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 min-h-screen flex items-center justify-center"><div class="bg-white rounded-lg shadow p-8 w-full max-w-sm"><h2 class="text-2xl font-bold mb-4 text-blue-700">Admin Login</h2><form method="post" class="space-y-4"><input type="password" name="password" class="border rounded px-3 py-2 w-full" placeholder="Admin Password" required><button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full" type="submit">Login</button></form>{% if error %}<div class="text-red-600 mt-2">{{ error }}</div>{% endif %}</div></body></html>''', error=error)

@bp.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.dashboard'))

@bp.route('/', methods=['GET'])
def dashboard():
    db = get_db()
    cursor = db.execute('SELECT pattern, type, target FROM redirects ORDER BY pattern ASC')
    shortcuts = [dict(pattern=row[0], type=row[1], target=row[2]) for row in cursor.fetchall()]
    return render_template_string(DASHBOARD_TEMPLATE, shortcuts=shortcuts)

@bp.route('/create', methods=['POST'])
def dashboard_create():
    db = get_db()
    pattern = request.form['pattern']
    type_ = request.form['type']
    target = request.form['target']
    db.execute('INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)', (type_, pattern, target))
    db.commit()
    return redirect(url_for('main.dashboard'))

@bp.route('/delete/<path:subpath>', methods=['GET'])
def dashboard_delete(subpath):
    db = get_db()
    db.execute('DELETE FROM redirects WHERE pattern=?', (subpath,))
    db.commit()
    return redirect(url_for('main.dashboard'))

@bp.route('/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):
    db = get_db()
    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        cursor = db.execute('SELECT 1 FROM redirects WHERE pattern=?', (subpath,))
        exists = cursor.fetchone()
        if exists:
            db.execute('UPDATE redirects SET type=?, target=? WHERE pattern=?', (type_, target, subpath))
            db.commit()
            return f'Redirect for <b>{subpath}</b> updated! <a href="/{subpath}">Test it</a>'
        else:
            db.execute('INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)', (type_, subpath, target))
            db.commit()
            return f'Redirect for <b>{subpath}</b> created! <a href="/{subpath}">Test it</a>'
    else:
        cursor = db.execute('SELECT type, target FROM redirects WHERE pattern=?', (subpath,))
        row = cursor.fetchone()
        if not row:
            # Enhanced UI for new shortcut creation
            return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Create Shortcut</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">Create new shortcut: <span class="font-mono">{{ pattern }}</span></h2>
    <form method="post" class="space-y-4">
      <div>
        <label class="block mb-1 font-semibold">Type</label>
        <select name="type" class="border rounded px-3 py-2 w-full">
          <option value="static">Static</option>
          <option value="dynamic">Dynamic</option>
        </select>
      </div>
      <div>
        <label class="block mb-1 font-semibold">Target URL <span class="text-gray-500">(use {name} for dynamic)</span></label>
        <input type="text" name="target" class="border rounded px-3 py-2 w-full" placeholder="Target URL" required>
      </div>
      <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full" type="submit">Create Shortcut</button>
      <div class="mt-4 text-center">
        <a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a>
      </div>
    </form>
  </div>
</body>
</html>
''', pattern=subpath)
        # Enhanced UI for editing existing shortcut
        return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Edit Shortcut</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">Edit shortcut: <span class="font-mono">{{ pattern }}</span></h2>
    <form method="post" class="space-y-4">
      <div>
        <label class="block mb-1 font-semibold">Type</label>
        <select name="type" class="border rounded px-3 py-2 w-full">
          <option value="static" {% if type=='static' %}selected{% endif %}>Static</option>
          <option value="dynamic" {% if type=='dynamic' %}selected{% endif %}>Dynamic</option>
        </select>
      </div>
      <div>
        <label class="block mb-1 font-semibold">Target URL <span class="text-gray-500">(use {name} for dynamic)</span></label>
        <input type="text" name="target" class="border rounded px-3 py-2 w-full" value="{{ target }}" required>
      </div>
      <button class="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600 w-full" type="submit">Update Shortcut</button>
      <div class="mt-4 flex justify-between">
        <a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a>
        <a href="/{{ pattern }}" class="text-blue-600 hover:underline">Test Shortcut</a>
      </div>
    </form>
  </div>
</body>
</html>
''', pattern=subpath, type=row[0], target=row[1])

@bp.route('/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    db = get_db()
    cursor = db.execute('SELECT target FROM redirects WHERE type = ? AND pattern = ?', ('static', subpath))
    row = cursor.fetchone()
    if row:
        if get_auto_redirect_delay() > 0:
            return render_template_string('<html><head><meta http-equiv="refresh" content="{{ delay }};url={{ url }}"></head><body>Redirecting to <a href="{{ url }}">{{ url }}</a> in {{ delay }} seconds...</body></html>', url=row[0], delay=get_auto_redirect_delay())
        return redirect(row[0], code=302)
    cursor = db.execute('SELECT pattern, target FROM redirects WHERE type = ?', ('dynamic',))
    for pattern, target in cursor.fetchall():
        if subpath.startswith(pattern + "/"):
            variable = subpath[len(pattern)+1:]
            dest_url = re.sub(r"\{\w+\}", variable, target)
            if get_auto_redirect_delay() > 0:
                return render_template_string('<html><head><meta http-equiv="refresh" content="{{ delay }};url={{ url }}"></head><body>Redirecting to <a href="{{ url }}">{{ url }}</a> in {{ delay }} seconds...</body></html>', url=dest_url, delay=get_auto_redirect_delay())
            return redirect(dest_url, code=302)
    # Not found: redirect to edit page for creation
    return redirect(url_for('main.edit_redirect', subpath=subpath), code=302)
