import logging
from datetime import datetime, timezone

from .error_routes import bp as error_bp
from .redirection_routes import bp as redirection_bp
from .routes import bp as route_bp
from .upstream_routes import bp as upstream_bp
from .version_routes import bp as version_bp
from .. import CONSTANTS
from ..config import config

logger = logging.getLogger(__name__)

ALL_APP_BLUEPRINTS = [
    route_bp,
    version_bp,
    error_bp,
    redirection_bp,
    upstream_bp

]

def register_blueprints(app):
    for bp in ALL_APP_BLUEPRINTS:
        app.register_blueprint(bp)
        logger.debug(f"Registered blueprint: {bp.name}")

    @app.context_processor
    def inject_now():
        # Try to get version string (same logic as version page)
        try:
            import subprocess
            commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip()
            commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
            version = f"v2.{commit_count}.{commit_hash}"
        except Exception as e:
            version = 'unknown'
            logger.debug(f"Could not determine version from git: {e}")

        redis_connected = bool(config.redis_enabled)


        return {'now': lambda: datetime.now(timezone.utc), 'version': version, 'redis_connected': redis_connected,
                'constants': CONSTANTS}

