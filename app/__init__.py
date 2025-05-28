from flask import Flask
from .utils import get_db, get_port, init_redis_from_config, app_startup_banner, init_upstream_cache_table
import secrets

def create_app():
    app = Flask(__name__)
    # Set secret key for session management
    app.secret_key = secrets.token_urlsafe(32)

    from .routes import bp
    from .version import bp_version
    app.register_blueprint(bp)
    app.register_blueprint(bp_version)

    with app.app_context():
        app.config['port'] = get_port()

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(app, '_database', None)
        if db is not None:
            db.close()

    def init_db():
        with app.app_context():
            db = get_db()
            cursor = db.cursor()

            # Check if 'redirects' table exists before creating it
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='redirects'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("🛠 Initializing 'redirects' table...")

                # Create redirects table only if it does not exist
                cursor.execute('''
                    CREATE TABLE redirects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        pattern TEXT NOT NULL,
                        target TEXT NOT NULL
                    )
                ''')
                db.commit()

            # Call to initialize upstream cache table
            init_upstream_cache_table(db)

    app.init_db = init_db


    return app

def run_standalone_startup(app):
    init_redis_from_config()
    app_startup_banner(app)
    app.init_db()
