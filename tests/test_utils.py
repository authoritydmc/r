import os
import tempfile
import sqlite3
import pytest
from app import utils
from flask import Flask, g

@pytest.fixture
def app():
    app = Flask(__name__)
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    utils.DATABASE = db_path
    # Create the DB and keep a reference to the test-created connection
    with app.app_context():
        db = sqlite3.connect(db_path)
        db.execute('CREATE TABLE IF NOT EXISTS redirects (pattern TEXT PRIMARY KEY, target TEXT, type TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.commit()
        db.close()  # Close the test-created connection
    yield app
    # Properly close the utils connection inside an app context
    with app.app_context():
        if hasattr(g, '_database') and g._database:
            g._database.close()
    os.close(db_fd)
    import gc
    gc.collect()  # Force garbage collection to release file handles
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

# --- Tests ---
def test_set_and_get_config(app):
    with app.app_context():
        utils.set_config('test_key', 'test_value')
        assert utils.get_config('test_key') == 'test_value'

def test_increment_and_get_access_count(app):
    with app.app_context():
        db = utils.get_db()
        db.execute('INSERT INTO redirects (pattern, target, type) VALUES (?, ?, ?)', ('foo', 'http://example.com', 'static'))
        db.commit()
        assert utils.get_access_count('foo') == 0
        utils.increment_access_count('foo')
        assert utils.get_access_count('foo') == 1
        utils.increment_access_count('foo')
        assert utils.get_access_count('foo') == 2

def test_get_created_updated(app):
    with app.app_context():
        db = utils.get_db()
        db.execute('INSERT INTO redirects (pattern, target, type, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                   ('bar', 'http://example.com', 'static', '2024-01-01', '2024-01-02'))
        db.commit()
        created, updated = utils.get_created_updated('bar')
        assert created == '2024-01-01'
        assert updated == '2024-01-02'
