import argparse
from app import create_app
from app.config import config
import logging

logger = logging.getLogger(__name__)
config.start_mode = 'Local App.py MODE'
app = create_app()

if __name__ == "__main__":
    logger.info("🚀 Running Flask Application from app.py")
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    args = parser.parse_args()
    mode = "DEV" if args.debug else "PROD"
    app.run(debug=args.debug, host="0.0.0.0", port=app.config['port'])
