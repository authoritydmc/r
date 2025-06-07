import sys
import os
from flask import Flask

# Ensure app/ is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app.routes.version_routes


def create_app():
    flask_app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../app/templates'))
    flask_app.secret_key = 'test'
    flask_app.register_blueprint(app.routes.routes.version.bp_version)
    return flask_app

def test_version_route_runs(monkeypatch):
    """Test that /version route runs and returns 200."""
    app = create_app()
    client = app.test_client()
    # Patch subprocess to avoid git dependency
    monkeypatch.setattr('subprocess.check_output', lambda *a, **k: '1234' if 'rev-list' in a[0] else 'abc123' if 'rev-parse' in a[0] else '2025-05-23')
    monkeypatch.setattr('app.version.get_port', lambda: 5000)
    monkeypatch.setattr('app.version.get_accessible_urls', lambda port: [f'http://localhost:{port}/'])
    resp = client.get('/version')
    assert resp.status_code == 200
    assert b'Version' in resp.data
    assert b'localhost' in resp.data

def test_version_route_handles_git_failure(monkeypatch):
    """Test that /version route works even if git commands fail."""
    app = create_app()
    client = app.test_client()
    monkeypatch.setattr('subprocess.check_output', lambda *a, **k: (_ for _ in ()).throw(Exception('fail')))
    monkeypatch.setattr('app.version.get_port', lambda: 5000)
    monkeypatch.setattr('app.version.get_accessible_urls', lambda port: [f'http://localhost:{port}/'])
    resp = client.get('/version')
    assert resp.status_code == 200
    assert b'unknown' in resp.data
