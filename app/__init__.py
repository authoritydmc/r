import json
from flask import Flask
from flask_migrate import Migrate
import logging
from model import  db
from .routes import ALL_APP_BLUEPRINTS
from .utils.utils import get_db_uri, get_port, init_redis_from_config, init_upstream_cache_table
from .utils.startup import app_startup_banner
import secrets


# Get a logger instance for this module
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_urlsafe(32)
    # Setup DB URL :
    logger.info(    "DB URL ",get_db_uri())
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
    db.init_app(app)
    migrate = Migrate(app, db)
    for bp in ALL_APP_BLUEPRINTS:
        app.register_blueprint(bp)
        logger.info(f"Registered blueprint: {bp.name}")

    with app.app_context():
        app.config['port'] = get_port()
        db.create_all()
    app_startup_banner(app)
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
