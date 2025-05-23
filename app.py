import sqlite3
from flask import Flask, redirect, abort, g
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

@app.route('/r/<path:subpath>')
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
    abort(404)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
