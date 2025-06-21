import pytest
from app import app as flask_app
from model.user_param import UserParam
from model.redirect import Redirect
from app import db

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_create_static_shortcut(client):
    resp = client.post('/edit/', data={
        'pattern': 'static-test',
        'type': 'static',
        'target': 'https://example.com/static'
    }, follow_redirects=True)
    assert resp.status_code == 200
    shortcut = Redirect.query.filter_by(pattern='static-test').first()
    assert shortcut is not None
    assert shortcut.target == 'https://example.com/static'
    assert shortcut.type == 'static'

def test_create_dynamic_shortcut(client):
    resp = client.post('/edit/', data={
        'pattern': 'dynamic-test/{foo}',
        'type': 'dynamic',
        'target': 'https://example.com/dyn/{foo}'
    }, follow_redirects=True)
    assert resp.status_code == 200
    shortcut = Redirect.query.filter_by(pattern='dynamic-test/{foo}').first()
    assert shortcut is not None
    assert shortcut.target == 'https://example.com/dyn/{foo}'
    assert shortcut.type == 'dynamic'

def test_create_user_dynamic_shortcut(client):
    # Create shortcut with user-dynamic param and param metadata
    resp = client.post('/edit/', data={
        'pattern': 'userdyn-test/[bar]',
        'type': 'user-dynamic',
        'target': 'https://example.com/userdyn/[bar]'
    }, follow_redirects=True)
    assert resp.status_code == 200
    shortcut = Redirect.query.filter_by(pattern='userdyn-test/[bar]').first()
    assert shortcut is not None
    assert shortcut.target == 'https://example.com/userdyn/[bar]'
    assert shortcut.type == 'user-dynamic'
    # Add param metadata for this shortcut
    param = UserParam(shortcut_pattern='userdyn-test/[bar]', param_name='bar', description='Bar param', required=True)
    db.session.add(param)
    db.session.commit()
    found = UserParam.query.filter_by(shortcut_pattern='userdyn-test/[bar]', param_name='bar').first()
    assert found is not None
    assert found.description == 'Bar param'
    assert found.required is True
