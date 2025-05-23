from app import create_app
from app.utils import get_port

app = create_app()

if __name__ == "__main__":
    print("\n==============================")
    print("URL Shortener & Redirector starting up...")
    print(f"Running on port: {app.config['port']}")
    print("\n[INFO] If you are running this in Docker:")
    print("  - Map the container port to your desired host port using -p <host_port>:<container_port>.")
    print("  - For production, use -p 80:80 or a reverse proxy for clean URLs (e.g., http://r/shortcut).\n")
    print("  - Mount your data directory with -v ./data:/app/data to persist shortcuts.")
    print("  - The database file will be at /app/data/redirects.db inside the container.\n")
    print("[INFO] For local testing, access: http://localhost:<port>/\n")
    print("==============================\n")
    app.init_db()
    app.run(debug=True,host="0.0.0.0", port=app.config['port'])