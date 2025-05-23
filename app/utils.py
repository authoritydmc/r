import os
import sqlite3
import json
from flask import g

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'redirects.db')

# --- Add access_count to schema if missing ---
def ensure_access_count_column():
    db = get_db()
    try:
        db.execute('ALTER TABLE redirects ADD COLUMN access_count INTEGER DEFAULT 0')
        db.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

# --- Add columns for audit logging if missing ---
def ensure_audit_columns():
    db = get_db()
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

CREATE_FORM = '''
<!DOCTYPE html>
<html><body>
<h2>Create new redirect for: <code>{{ pattern }}</code></h2>
<form method="post">
  <label>Type:</label>
  <select name="type">
    <option value="static">Static</option>
    <option value="dynamic">Dynamic</option>
  </select><br><br>
  <label>Target URL (use {name} for dynamic):</label><br>
  <input type="text" name="target" style="width:400px" required><br><br>
  <button type="submit">Create Redirect</button>
</form>
</body></html>
'''

EDIT_FORM = '''
<!DOCTYPE html>
<html><body>
<h2>Edit redirect for: <code>{{ pattern }}</code></h2>
<form method="post">
  <label>Type:</label>
  <select name="type">
    <option value="static" {% if type=='static' %}selected{% endif %}>Static</option>
    <option value="dynamic" {% if type=='dynamic' %}selected{% endif %}>Dynamic</option>
  </select><br><br>
  <label>Target URL (use {name} for dynamic):</label><br>
  <input type="text" name="target" style="width:400px" value="{{ target }}" required><br><br>
  <button type="submit">Update Redirect</button>
</form>
</body></html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>URL Shortener Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
  <div class="max-w-3xl mx-auto py-8">
    <h1 class="text-3xl font-bold mb-6 text-center text-blue-700">URL Shortener/Redirector Dashboard</h1>
    <div class="flex flex-wrap justify-center gap-4 mb-8">
      <a href="/version" class="bg-gray-200 px-4 py-2 rounded hover:bg-blue-200 text-blue-700 font-semibold">Version</a>
      <a href="/tutorial" class="bg-gray-200 px-4 py-2 rounded hover:bg-blue-200 text-blue-700 font-semibold">Dynamic URL Tutorial</a>
      <a href="https://github.com/authoritydmc/r/blob/main/README.md" target="_blank" class="bg-gray-200 px-4 py-2 rounded hover:bg-blue-200 text-blue-700 font-semibold">GitHub README</a>
    </div>
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-xl font-semibold mb-4">All Shortcuts</h2>
      <table class="min-w-full table-auto text-left">
        <thead>
          <tr>
            <th class="px-4 py-2">Shortcut</th>
            <th class="px-4 py-2">Type</th>
            <th class="px-4 py-2">Target</th>
            <th class="px-4 py-2">Accesses</th>
            <th class="px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
        {% for shortcut in shortcuts %}
          <tr class="border-t">
            <td class="px-4 py-2 font-mono">{{ shortcut['pattern'] }}</td>
            <td class="px-4 py-2">{{ shortcut['type'] }}</td>
            <td class="px-4 py-2 break-all"><a class="text-blue-600 underline" href="{{ shortcut['target'] }}" target="_blank">{{ shortcut['target'] }}</a></td>
            <td class="px-4 py-2 text-center">{{ shortcut['access_count'] }}</td>
            <td class="px-4 py-2">
              <a class="text-green-600 hover:underline mr-2" href="/{{ shortcut['pattern'] }}" target="_blank">Go</a>
              <a class="text-yellow-600 hover:underline mr-2" href="/edit/{{ shortcut['pattern'] }}">Edit</a>
              <a class="text-red-600 hover:underline" href="/delete/{{ shortcut['pattern'] }}" onclick="return confirm('Delete this shortcut?');">Delete</a>
            </td>
          </tr>
        {% else %}
          <tr><td colspan="5" class="px-4 py-2 text-center text-gray-500">No shortcuts found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
'''

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    ensure_access_count_column()
    ensure_audit_columns()
    return db

def get_config(key, default=None):
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL)
    """)
    db.commit()
    cursor = db.execute('SELECT value FROM config WHERE key=?', (key,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    # If not found, set default
    set_config(key, default)
    return default

def set_config(key, value):
    db = get_db()
    db.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, json.dumps(value)))
    db.commit()

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
