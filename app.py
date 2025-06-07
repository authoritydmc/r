import argparse
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Running app.py")
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    args = parser.parse_args()
    mode = "DEV" if args.debug else "PROD"
    print("\n==============================\n")
    app.run(debug=args.debug, host="0.0.0.0", port=app.config['port'])
