import logging
import secrets
from flask import Flask
from flask_migrate import Migrate
from model import db

from .routes import register_blueprints
from .utils.utils import get_db_uri, get_port
from .utils.startup import app_startup_banner

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app_startup_banner(app)
    app.secret_key = secrets.token_urlsafe(32)

    # Setup DB URL
    db_uri = get_db_uri()
    if not db_uri:
        logger.error("Database URI could not be determined. Exiting application.")
        raise RuntimeError("Invalid DB URI")

    logger.info(f"Initializing database with URI: {db_uri}")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register all routes
    register_blueprints(app)

    with app.app_context():
        app.config['port'] = get_port()
        try:
            db.create_all()  # If using Flask-Migrate, this may not be needed
        except Exception as e:
            logger.exception("Database initialization failed.", exc_info=e)
            raise

    # Display application startup details


    return app


# def run_standalone_startup(app):
#     """Standalone startup routine for debugging and route discovery."""
#     app_startup_banner(app)
#
#     try:
#         routes = [
#             {"route": rule.rule, "methods": list(rule.methods), "endpoint": rule.endpoint}
#             for rule in app.url_map.iter_rules()
#         ]
#
#         file_path = "urlMap.json"
#         with open(file_path, "w") as f:
#             json.dump(routes, f, indent=4)
#
#         logger.info(f"Route mappings saved to {file_path}")
#
#     except Exception as e:
#         logger.exception("Failed to generate URL map.", exc_info=e)
