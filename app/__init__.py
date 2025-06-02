import json
from flask import Flask
from flask_migrate import Migrate

from model import  db
from .utils import get_db_uri, get_port, init_redis_from_config, app_startup_banner, init_upstream_cache_table
import secrets

def create_app():
    app = Flask(__name__)
    # Set secret key for session management
    app.secret_key = secrets.token_urlsafe(32)
    # Setup DB URL :
    print("DB URL ",get_db_uri())
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
    db.init_app(app)
    migrate = Migrate(app, db)
    from .routes import bp
    from .version import bp_version
    app.register_blueprint(bp)
    app.register_blueprint(bp_version)

    with app.app_context():
        app.config['port'] = get_port()
        db.create_all()
    return app

def run_standalone_startup(app):
    init_redis_from_config()
    app_startup_banner(app)
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "route": rule.rule,
            "methods": list(rule.methods),
            "endpoint": rule.endpoint
        })

    # Write to urlMap.json
    with open("urlMap.json", "w") as f:
        json.dump(routes, f, indent=4)
