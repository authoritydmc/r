import os
import sqlite3
import json
from flask import g

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'redirects.db')
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'redirect.config.json')

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
    <div class="bg-white rounded-lg shadow p-6 mb-8">
      <form class="flex flex-col md:flex-row gap-4" method="post" action="/create">
        <input name="pattern" class="border rounded px-3 py-2 flex-1" placeholder="Shortcut (e.g. google)" required>
        <select name="type" class="border rounded px-3 py-2">
          <option value="static">Static</option>
          <option value="dynamic">Dynamic</option>
        </select>
        <input name="target" class="border rounded px-3 py-2 flex-1" placeholder="Target URL (use {name} for dynamic)" required>
        <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700" type="submit">Create Shortcut</button>
      </form>
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
          <tr class="border-t">
            <td class="px-4 py-2 font-mono">{{ shortcut['pattern'] }}</td>
            <td class="px-4 py-2">{{ shortcut['type'] }}</td>
            <td class="px-4 py-2 break-all"><a class="text-blue-600 underline" href="{{ shortcut['target'] }}" target="_blank">{{ shortcut['target'] }}</a></td>
            <td class="px-4 py-2">
              <a class="text-green-600 hover:underline mr-2" href="/r/{{ shortcut['pattern'] }}" target="_blank">Go</a>
              <a class="text-yellow-600 hover:underline mr-2" href="/r/edit/{{ shortcut['pattern'] }}">Edit</a>
              <a class="text-red-600 hover:underline" href="/delete/{{ shortcut['pattern'] }}" onclick="return confirm('Delete this shortcut?');">Delete</a>
            </td>
          </tr>
        {% else %}
          <tr><td colspan="4" class="px-4 py-2 text-center text-gray-500">No shortcuts found.</td></tr>
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
    return db

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"auto_redirect_delay": 0, "port": 80}, f)
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)
config = load_config()
