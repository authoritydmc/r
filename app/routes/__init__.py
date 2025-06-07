# Import individual blueprint instances from their respective modules
# Assuming you have:
# - app/routes/main.py which defines 'bp' for main routes
# - app/routes/admin.py which defines 'bp' for admin routes (or 'admin_bp')
from datetime import datetime, timezone

from .routes import bp as route_bp # Import as main_bp to avoid naming conflicts if multiple 'bp' exist
from .version_routes import bp as version_bp # And assuming you have an admin.py with its own blueprint
import logging
from .error_routes import bp as error_bp
from .. import CONSTANTS
from ..utils import utils
from .redirection_routes import bp as redirection_bp
from .upstream_routes import bp as upstream_bp

logger = logging.getLogger(__name__)
# You can define a list of all blueprints to make registration cleaner
# This list will be imported by your main app's create_app() function
ALL_APP_BLUEPRINTS = [
    route_bp,
    version_bp,
    error_bp,
    redirection_bp,
    upstream_bp

]

# Optional: You could also define a function to register them, but
# exposing the list is often simpler when you're just registering them once in create_app.
# def register_blueprints(app):
#     """Registers all blueprints from this package with the given Flask application."""
#     for blueprint in ALL_APP_BLUEPRINTS:
#         app.register_blueprint(blueprint)
def register_blueprints(app):
    for bp in ALL_APP_BLUEPRINTS:
        app.register_blueprint(bp)
        logger.info(f"Registered blueprint: {bp.name}")

    @app.context_processor
    def inject_now():
        # Try to get version string (same logic as version page)
        try:
            import subprocess
            commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip()
            commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
            version = f"v1.{commit_count}.{commit_hash}"
        except Exception as e:
            version = 'unknown'
            logger.debug(f"Could not determine version from git: {e}")

        # Add redis_connected context (already relies on _redis_enabled from utils)
        redis_connected = bool(utils.redis_enabled)  # _redis_enabled is now a global var from utils


        return {'now': lambda: datetime.now(timezone.utc), 'version': version, 'redis_connected': redis_connected,
                'constants': CONSTANTS}

