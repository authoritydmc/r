from flask import Blueprint, render_template_string, request, redirect, url_for, g, session, abort
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
    cursor = db.execute('SELECT pattern, type, target, access_count FROM redirects ORDER BY pattern ASC')
    shortcuts = [dict(pattern=row[0], type=row[1], target=row[2], access_count=row[3] if row[3] is not None else 0) for row in cursor.fetchall()]
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
                return render_template_string('''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Delete Shortcut</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 min-h-screen flex items-center justify-center"><div class="bg-white rounded-lg shadow p-8 w-full max-w-sm"><h2 class="text-2xl font-bold mb-4 text-red-700">Delete Shortcut</h2><form method="post" class="space-y-4"><input type="password" name="password" class="border rounded px-3 py-2 w-full" placeholder="Admin Password" required><button class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 w-full" type="submit">Delete</button></form>{% if error %}<div class="text-red-600 mt-2">{{ error }}</div>{% endif %}<div class="mt-4 text-center"><a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a></div></div></body></html>''', error=error)
        else:
            return render_template_string('''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Delete Shortcut</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 min-h-screen flex items-center justify-center"><div class="bg-white rounded-lg shadow p-8 w-full max-w-sm"><h2 class="text-2xl font-bold mb-4 text-red-700">Delete Shortcut</h2><form method="post" class="space-y-4"><input type="password" name="password" class="border rounded px-3 py-2 w-full" placeholder="Admin Password" required><button class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 w-full" type="submit">Delete</button></form><div class="mt-4 text-center"><a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a></div></div></body></html>''')
    else:
        db.execute('DELETE FROM redirects WHERE pattern=?', (subpath,))
        db.commit()
        return redirect(url_for('main.dashboard'))

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
            return f'Redirect for <b>{subpath}</b> updated! <a href="/{subpath}">Test it</a>'
        else:
            db.execute('INSERT INTO redirects (type, pattern, target, created_at, updated_at, created_ip, updated_ip) VALUES (?, ?, ?, ?, ?, ?, ?)', (type_, subpath, target, now, now, ip, ip))
            db.commit()
            return f'Redirect for <b>{subpath}</b> created! <a href="/{subpath}">Test it</a>'
    else:
        cursor = db.execute('SELECT type, target FROM redirects WHERE pattern=?', (subpath,))
        row = cursor.fetchone()
        access_count = get_access_count(subpath)
        created_at, updated_at = get_created_updated(subpath)
        if not row:
            # Enhanced UI for new shortcut creation
            return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Create Shortcut</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    function suggestTypeAndUrl() {
      const targetInput = document.getElementById('target');
      const typeSelect = document.getElementById('type');
      let val = targetInput.value.trim();
      // Suggest https:// if not present
      if (val && !/^https?:\/\//i.test(val)) {
        targetInput.value = 'https://' + val;
        val = targetInput.value;
      }
      // Suggest type
      const suggestion = document.getElementById('suggestion');
      if (val.includes('{')) {
        typeSelect.value = 'dynamic';
        suggestion.innerHTML = '<div class="bg-blue-100 border border-blue-300 text-blue-800 px-4 py-2 rounded mb-2">This will be a <b>Dynamic</b> shortcut. Use curly braces for variables, e.g. <span class="font-mono">{name}</span>.</div>';
      } else {
        typeSelect.value = 'static';
        suggestion.innerHTML = '<div class="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mb-2">This will be a <b>Static</b> shortcut. The URL will always redirect to the same address.</div>';
      }
    }
  </script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">Create new shortcut: <span class="font-mono">{{ pattern }}</span></h2>
    <form method="post" class="space-y-4" oninput="suggestTypeAndUrl()">
      <div id="suggestion"></div>
      <div>
        <label class="block mb-1 font-semibold">Type</label>
        <select name="type" id="type" class="border rounded px-3 py-2 w-full">
          <option value="static">Static</option>
          <option value="dynamic">Dynamic</option>
        </select>
      </div>
      <div>
        <label class="block mb-1 font-semibold">Target URL <span class="text-gray-500">(use {name} for dynamic)</span></label>
        <input type="text" name="target" id="target" class="border rounded px-3 py-2 w-full" placeholder="Target URL" required>
      </div>
      <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full" type="submit">Create Shortcut</button>
      <div class="mt-4 text-center">
        <a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a>
      </div>
    </form>
  </div>
  <script>suggestTypeAndUrl();</script>
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
  <script>
    function suggestTypeAndUrl() {
      const targetInput = document.getElementById('target');
      const typeSelect = document.getElementById('type');
      let val = targetInput.value.trim();
      // Suggest https:// if not present
      if (val && !/^https?:\/\//i.test(val)) {
        targetInput.value = 'https://' + val;
        val = targetInput.value;
      }
      // Suggest type
      const suggestion = document.getElementById('suggestion');
      if (val.includes('{')) {
        typeSelect.value = 'dynamic';
        suggestion.innerHTML = '<div class="bg-blue-100 border border-blue-300 text-blue-800 px-4 py-2 rounded mb-2">This is a <b>Dynamic</b> shortcut. Use curly braces for variables, e.g. <span class="font-mono">{name}</span>.</div>';
      } else {
        typeSelect.value = 'static';
        suggestion.innerHTML = '<div class="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mb-2">This is a <b>Static</b> shortcut. The URL will always redirect to the same address.</div>';
      }
    }
  </script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">Edit shortcut: <span class="font-mono">{{ pattern }}</span></h2>
    <div class="mb-2 text-gray-600">Access count: <span class="font-mono">{{ access_count }}</span></div>
    <div class="mb-2 text-gray-600">Created: <span class="font-mono">{{ created_at if created_at else 'N/A' }}</span></div>
    <div class="mb-2 text-gray-600">Last updated: <span class="font-mono">{{ updated_at if updated_at else 'N/A' }}</span></div>
    <form method="post" class="space-y-4" oninput="suggestTypeAndUrl()">
      <div id="suggestion"></div>
      <div>
        <label class="block mb-1 font-semibold">Type</label>
        <select name="type" id="type" class="border rounded px-3 py-2 w-full">
          <option value="static" {% if type=='static' %}selected{% endif %}>Static</option>
          <option value="dynamic" {% if type=='dynamic' %}selected{% endif %}>Dynamic</option>
        </select>
      </div>
      <div>
        <label class="block mb-1 font-semibold">Target URL <span class="text-gray-500">(use {name} for dynamic)</span></label>
        <input type="text" name="target" id="target" class="border rounded px-3 py-2 w-full" value="{{ target }}" required>
      </div>
      <button class="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600 w-full" type="submit">Update Shortcut</button>
      <div class="mt-4 flex justify-between">
        <a href="/" class="text-gray-500 hover:underline">Back to Dashboard</a>
        <a href="/{{ pattern }}" class="text-blue-600 hover:underline">Test Shortcut</a>
      </div>
    </form>
  </div>
  <script>suggestTypeAndUrl();</script>
</body>
</html>
''', pattern=subpath, type=row[0], target=row[1], access_count=access_count, created_at=created_at, updated_at=updated_at)

@bp.route('/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    db = get_db()
    cursor = db.execute('SELECT target FROM redirects WHERE type = ? AND pattern = ?', ('static', subpath))
    row = cursor.fetchone()
    if row:
        increment_access_count(subpath)
        if get_auto_redirect_delay() > 0:
            return render_template_string('<html><head><meta http-equiv="refresh" content="{{ delay }};url={{ url }}"></head><body>Redirecting to <a href="{{ url }}">{{ url }}</a> in {{ delay }} seconds...</body></html>', url=row[0], delay=get_auto_redirect_delay())
        return redirect(row[0], code=302)
    # Check if subpath matches a dynamic pattern but is missing the variable
    cursor = db.execute('SELECT pattern, target FROM redirects WHERE type = ?', ('dynamic',))
    for pattern, target in cursor.fetchall():
        import re as _re
        match = _re.search(r'\{(\w+)\}', target)
        var_name = match.group(1) if match else 'name'
        if subpath == pattern:
            # User accessed /meetwith instead of /meetwith/raj
            example_var = 'yourvalue'
            example_url = f'/{pattern}/' + example_var
            example_target = target.replace(f'{{{var_name}}}', example_var)
            return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dynamic Shortcut Usage</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-blue-50 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-lg">
    <div class="bg-blue-100 border border-blue-300 text-blue-800 px-4 py-2 rounded mb-4">
      <b>This is a dynamic shortcut:</b> <span class="font-mono">/{{ pattern }}/&#123;{{ var_name }}&#125;</span><br>
      To use it, add a value after <span class="font-mono">/{{ pattern }}/</span>.<br>
      <div class="mt-2">Example: <span class="font-mono">/{{ pattern }}/yourvalue</span> will redirect to <span class="font-mono">{{ example_target }}</span> (where <span class="font-mono">&#123;{{ var_name }}&#125;</span> is replaced by <span class="font-mono">yourvalue</span>).</div>
    </div>
    <div class="mt-6 text-center">
      <a href="/" class="text-blue-600 hover:underline">Back to Dashboard</a>
    </div>
  </div>
</body>
</html>''', pattern=pattern, var_name=var_name, example_target=example_target)
        if subpath.startswith(pattern + "/"):
            variable = subpath[len(pattern)+1:]
            dest_url = _re.sub(r"\{\w+\}", variable, target)
            increment_access_count(pattern)
            if get_auto_redirect_delay() > 0:
                return render_template_string('<html><head><meta http-equiv="refresh" content="{{ delay }};url={{ url }}"></head><body>Redirecting to <a href="{{ url }}">{{ url }}</a> in {{ delay }} seconds...</body></html>', url=dest_url, delay=get_auto_redirect_delay())
            return redirect(dest_url, code=302)
    # Not found: redirect to edit page for creation
    return redirect(url_for('main.edit_redirect', subpath=subpath), code=302)

@bp.route('/tutorial', methods=['GET'])
def tutorial():
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dynamic URL Tutorial</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-lg shadow p-8 w-full max-w-2xl">
    <h2 class="text-2xl font-bold mb-4 text-blue-700">How to Create Dynamic Shortcuts</h2>
    <div class="mb-4">
      <div class="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mb-2">
        <b>New: URL creation is now only available from the <span class="font-mono">Edit</span> page.</b><br>
        To create a shortcut, simply visit <span class="font-mono">/edit/&lt;shortcut&gt;</span> (e.g. <span class="font-mono">/edit/meetwith</span>) and use the form there.
      </div>
      <div class="bg-blue-100 border border-blue-300 text-blue-800 px-4 py-2 rounded mb-2">
        <b>Real-time suggestions:</b> The edit page will automatically detect if your shortcut is <b>Static</b> or <b>Dynamic</b> and show a colored message. It will also add <span class="font-mono">https://</span> to your target URL if you forget it.
      </div>
    </div>
    <ol class="list-decimal list-inside mb-4 space-y-2">
      <li>
        <b>Go to the edit page</b> for your shortcut (e.g. <span class="font-mono">/edit/meetwith</span>).
      </li>
      <li>
        <b>Type your target URL</b>. If you use curly braces (e.g. <span class="font-mono">{name}</span>), it will be a <b>Dynamic</b> shortcut. Otherwise, it will be <b>Static</b>.
      </li>
      <li>
        <b>Let the form help you:</b> The page will show a green or blue box to indicate the type, and will add <span class="font-mono">https://</span> if missing.
      </li>
      <li>
        <b>Save the shortcut</b>. Now, visiting <span class="font-mono">/meetwith/raj</span> will redirect to <span class="font-mono">https://g.co/meet/raj</span> if you used <span class="font-mono">https://g.co/meet/{name}</span> as the target.
      </li>
    </ol>
    <div class="mb-4">
      <b>Tip:</b> You can use any variable name inside curly braces (e.g. <span class="font-mono">{user}</span>, <span class="font-mono">{id}</span>). The part after the shortcut in the URL will be substituted in place of the variable.
    </div>
    <div class="mt-6 text-center">
      <a href="/" class="text-blue-600 hover:underline">Back to Dashboard</a>
    </div>
  </div>
</body>
</html>
''')
