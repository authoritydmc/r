from app import create_app
from app.utils import get_port

app = create_app()

if __name__ == "__main__":
    app.init_db()
    app.run(host="0.0.0.0", port=app.config['port'])