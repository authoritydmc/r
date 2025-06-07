import os
import gevent.monkey
gevent.monkey.patch_all()

import logging
import secrets
from flask import Flask
from flask_migrate import Migrate
from .config import config
from model import db

from .routes import register_blueprints
from .utils.utils import get_db_uri, get_port
from .utils.startup import app_startup_banner

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app_startup_banner(app)
    if config.redis_enabled:
        config.init_redis()

    app.secret_key = secrets.token_urlsafe(32)

    # Setup DB URL
    db_uri = get_db_uri()
    if not db_uri:
        logger.error("Database URI could not be determined. Exiting application.")
        raise RuntimeError("Invalid DB URI")

    logger.info(f"Initializing database with URI: {db_uri}")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True


    try:
        db.init_app(app)
        logger.info("✅ Database connection successful!")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

    # Initialize database and migrations
   
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


