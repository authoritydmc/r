import os
import sqlite3
import json
from flask import g

# Ensure data directory exists (cross-platform)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE = os.path.join(DATA_DIR, 'redirects.db')
CONFIG_FILE = os.path.join(DATA_DIR, 'redirect.json.config')

# --- JSON config helpers ---
def _load_config():
    if not os.path.exists(CONFIG_FILE):
        import secrets
        import string
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        print(f"Generated password :{random_pwd} for admin access")
        default = {
            "port": 80,
            "auto_redirect_delay":3,
            "admin_password": random_pwd,
            "delete_requires_password": True
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
    <h1 class="text-3xl font-bold mb-6 text-center text-blue-700">
      <a href="/" class="hover:underline flex items-center justify-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="inline w-8 h-8 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m4 4h1a2 2 0 002-2V7a2 2 0 00-2-2h-6a2 2 0 00-2 2v7a2 2 0 002 2h1" /></svg>
        URL Shortener/Redirector Dashboard
      </a>
    </h1>
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
            <th class="px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
        {% for shortcut in shortcuts %}
          <tr class="border-t align-top">
            <td class="px-4 py-2 font-mono align-top">
              <div class="flex items-center gap-2">
                {% if shortcut['type'] == 'static' %}
                  <span title="Static shortcut"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 14.828a4 4 0 010-5.656m1.415 1.414a2 2 0 010 2.828m-2.829-2.828a6 6 0 018.485 8.485l-3.536 3.535a6 6 0 01-8.485-8.485l3.535-3.535a2 2 0 112.828 2.828l-3.535 3.535a2 2 0 102.828 2.828l3.535-3.535" /></svg></span>
                {% else %}
                  <span title="Dynamic shortcut"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg></span>
                {% endif %}
                {{ shortcut['pattern'] }}
              </div>
              <div class="text-xs text-gray-400 mt-1 flex items-center gap-4">
                <span title="Accesses" class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>{{ shortcut['access_count'] }}</span>
                <span title="Created" class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>{{ shortcut['created_at'] if shortcut['created_at'] else 'N/A' }}</span>
                <span title="Last updated" class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>{{ shortcut['updated_at'] if shortcut['updated_at'] else 'N/A' }}</span>
              </div>
            </td>
            <td class="px-4 py-2 align-top">
              {% if shortcut['type'] == 'static' %}
                <span title="Static shortcut"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 14.828a4 4 0 010-5.656m1.415 1.414a2 2 0 010 2.828m-2.829-2.828a6 6 0 018.485 8.485l-3.536 3.535a6 6 0 01-8.485-8.485l3.535-3.535a2 2 0 112.828 2.828l-3.535 3.535a2 2 0 102.828 2.828l3.535-3.535" /></svg></span>
              {% else %}
                <span title="Dynamic shortcut"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg></span>
              {% endif %}
            </td>
            <td class="px-4 py-2 break-all align-top"><a class="text-blue-600 underline" href="{{ shortcut['target'] }}" target="_blank">{{ shortcut['target'] }}</a></td>
            <td class="px-4 py-2 align-top">
              <a class="text-green-600 hover:underline mr-2" href="/{{ shortcut['pattern'] }}" target="_blank" title="Go"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg></a>
              <a class="text-yellow-600 hover:underline mr-2" href="/edit/{{ shortcut['pattern'] }}" title="Edit"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536M9 11l6 6M3 21h6a2 2 0 002-2v-6a2 2 0 00-2-2H3a2 2 0 00-2 2v6a2 2 0 002 2z" /></svg></a>
              <a class="text-red-600 hover:underline" href="/delete/{{ shortcut['pattern'] }}" onclick="return confirm('Delete this shortcut?');" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></a>
            </td>
          </tr>
        {% else %}
          <tr><td colspan="4" class="px-4 py-2 text-center text-gray-500">No shortcuts found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
      <div class="mt-6 p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
        <div class="font-semibold mb-1">Legend:</div>
        <div class="flex flex-wrap gap-6 items-center">
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-green-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 14.828a4 4 0 010-5.656m1.415 1.414a2 2 0 010 2.828m-2.829-2.828a6 6 0 018.485 8.485l-3.536 3.535a6 6 0 01-8.485-8.485l3.535-3.535a2 2 0 112.828 2.828l-3.535 3.535a2 2 0 102.828 2.828l3.535-3.535" /></svg>Static</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-blue-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>Dynamic</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>Accesses</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>Created</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>Last updated</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline mr-1 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>Go</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline mr-1 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536M9 11l6 6M3 21h6a2 2 0 002-2v-6a2 2 0 00-2-2H3a2 2 0 00-2 2v6a2 2 0 002 2z" /></svg>Edit</span>
          <span class="flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 inline mr-1 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>Delete</span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
'''

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
