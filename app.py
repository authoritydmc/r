import platform
import argparse
from app import create_app, run_standalone_startup

app = create_app()
run_standalone_startup(app)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prod", action="store_true", help="Run Flask in prod mode")
    args = parser.parse_args()
    mode = "PROD" if args.prod else "DEV"
    print("\n==============================\n")
    # app.init_db()
    app.run(debug=args.prod, host="0.0.0.0", port=app.config['port'])
