# wsgi.py

import platform
from app import create_app
from app.utils import init_redis_from_config, app_startup_banner

# Initialize Flask app
try:
    print("Running wsgi.py")
    app = create_app()
except Exception as e:
    import traceback
    print("\n[ERROR] Failed to initialize Flask app.\n")
    traceback.print_exc()
    raise

# # Print environment details and host setup tips
# app_startup_banner(app)
#
# # Expose app variable for Gunicorn
# # Gunicorn will look for: `wsgi:app`
