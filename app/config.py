# Get the project's root directory by going one level above 'app'
import os

import logging

from app.utils import running_in_docker

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create the 'data' folder at the project root level
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Set config file path
CONFIG_FILE = os.path.join(DATA_DIR, 'redirect.config.json')

logger.debug(f"Data directory created at: {DATA_DIR}")
logger.debug(f"Config file path set to: {CONFIG_FILE}")


def get_Default_Config():
    import secrets
    import string
    random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    logger.info(
        f"Generated password for admin access. Please check your console for the password if running for the first time.")
    logger.info(f"Admin Password: {random_pwd}")  # Log it at INFO level for visibility during first run

    return {
        "port": 80,
        "auto_redirect_delay": 3,
        "database": "sqlite:///redirects.db",
        "admin_password": random_pwd,
        "delete_requires_password": True,
        "upstreams": [],
        "redis": {
            "enabled": True,
            "host": "redis" if running_in_docker else "localhost",
            "port": 6379
        },
        "upstream_cache": {
            "enabled": True
        }
    }