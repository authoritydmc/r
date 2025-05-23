from flask import Flask
from .utils import get_db, config

def create_app():
    app = Flask(__name__)
    from .routes import bp
    from .version import bp_version
    app.register_blueprint(bp)
    app.register_blueprint(bp_version)

    app.config['port'] = config.get('port', 80)

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(app, '_database', None)
        if db is not None:
            db.close()

    def init_db():
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS redirects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                target TEXT NOT NULL
            )''')
            db.commit()
    app.init_db = init_db
    return app
