import sqlite3
from flask import Flask, redirect, abort, g, request, render_template_string
import re
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'redirects.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS redirects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'static' or 'dynamic'
            pattern TEXT NOT NULL, -- e.g. 'google' or 'meetwith'
            target TEXT NOT NULL -- e.g. 'https://google.com' or 'https://g.co/meet/{name}'
        )''')
        db.commit()

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

@app.route('/r/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    db = get_db()
    # Check static
    cursor = db.execute('SELECT target FROM redirects WHERE type = ? AND pattern = ?', ('static', subpath))
    row = cursor.fetchone()
    if row:
        return redirect(row[0], code=302)
    # Check dynamic
    cursor = db.execute('SELECT pattern, target FROM redirects WHERE type = ?', ('dynamic',))
    for pattern, target in cursor.fetchall():
        if subpath.startswith(pattern + "/"):
            variable = subpath[len(pattern)+1:]
            dest_url = re.sub(r"\{\w+\}", variable, target)
            return redirect(dest_url, code=302)
    # Not found: show create form
    return render_template_string(CREATE_FORM, pattern=subpath)

@app.route('/r/<path:subpath>', methods=['POST'])
def create_redirect(subpath):
    db = get_db()
    type_ = request.form['type']
    target = request.form['target']
    db.execute('INSERT INTO redirects (type, pattern, target) VALUES (?, ?, ?)', (type_, subpath, target))
    db.commit()
    return f'Redirect for <b>{subpath}</b> created! <a href="/r/{subpath}">Test it</a>'

@app.route('/r/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):
    db = get_db()
    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        db.execute('UPDATE redirects SET type=?, target=? WHERE pattern=?', (type_, target, subpath))
        db.commit()
        return f'Redirect for <b>{subpath}</b> updated! <a href="/r/{subpath}">Test it</a>'
    else:
        cursor = db.execute('SELECT type, target FROM redirects WHERE pattern=?', (subpath,))
        row = cursor.fetchone()
        if not row:
            return f'No redirect found for <b>{subpath}</b>. <a href="/r/{subpath}">Create it</a>'
        return render_template_string(EDIT_FORM, pattern=subpath, type=row[0], target=row[1])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
