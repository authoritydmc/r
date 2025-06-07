import json
import os
import logging
import secrets
import string
import redis


class Config:
    """Handles application configurations."""

    def __init__(self):
        """Initialize configuration settings."""
        # First setup paths to access config
        self.PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.PROJECT_ROOT, 'data')
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.CONFIG_FILE = os.path.join(self.DATA_DIR, 'redirect.config.json')
        # Detect Docker environment
        self.RUNNING_IN_DOCKER = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') is not None
        self.start_mode = "Gunicorn MODE"
        # Load basic config (used for logging level)
        temp_cfg = self.load_raw_config()

        # Setup logging with config or fallback level
        self.setup_logging(temp_cfg.get("log_level", "DEBUG"))

        # Now reload config fully (including Redis, etc.)
        self.logger.debug(f"Config file path: {self.CONFIG_FILE}")
        self.cfg = temp_cfg



        # Redis configuration
        self.redis_cfg = self.cfg.get('redis', {})
        self.redis_enabled = self.redis_cfg.get('enabled', False)
        self.redis_host = self.redis_cfg.get('host', 'redis')
        self.redis_port = int(self.redis_cfg.get('port', 6379))
        self.redis_client = None
        self.database=self.cfg.get('database')

    def get_configuration(self):
        return self.cfg

    def setup_logging(self, log_level_str):
        """Set up logging to print logs to the console with dynamic level."""
        level = getattr(logging, log_level_str.upper(), logging.DEBUG)
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=level
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Logging initialized with level: {log_level_str.upper()}")

    def load_raw_config(self):
        """Load the config or create default if needed, without logging."""
        if not os.path.exists(self.CONFIG_FILE) or os.path.getsize(self.CONFIG_FILE) == 0:
            try:
                default = self.get_default_config()
                with open(self.CONFIG_FILE, 'w') as f:
                    json.dump(default, f, indent=2)
                print(f"\n🔐 Admin Password (save this): {default['admin_password']}")
                return default
            except IOError:
                return {}

        try:
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}

    def get_redis_default_config(self):
        """Fetch Redis configurations dynamically."""
        try:
            redis_host = os.getenv('REDIS_HOST', 'redis' if self.RUNNING_IN_DOCKER else 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            return {
                "host": redis_host,
                "port": redis_port
            }
        except Exception as e:
            self.logger.error(f"❌ Error fetching Redis default config: {e}")
            return {
                "host": "localhost",
                "port": 6379
            }

    def init_redis(self):
        """Initialize Redis client and handle connection errors."""
        try:
            if not self.redis_enabled:
                self.logger.debug("🔗 Redis is disabled, skipping initialization.")
                return
            self.logger.debug(f"🔗 Initializing Redis client at {self.redis_host}:{self.redis_port}")
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=1
            )
            self.redis_client.ping() 

            self.logger.info(f"✅ Redis connected at {self.redis_host}:{self.redis_port}")
        except redis.exceptions.ConnectionError as e:
            self.logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_enabled = False
            self.redis_client = None
        except Exception as e:
            self.logger.exception("❌ Unexpected error initializing Redis.")
            self.redis_enabled = False
            self.redis_client = None

    def reconnect_redis(self):
        """Attempt to reconnect to Redis (e.g., after failure)."""
        if not self.redis_enabled:
            return
        self.logger.debug("🔄 Attempting Redis reconnection...")
        self.init_redis()

    def get_default_config(self):
        """Generate default config values including secure admin password."""
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        redis_default = self.get_redis_default_config()

        print("\n🔐 Admin password generated for first-time setup.")
        print(f"   Password: {random_pwd}")

        return {
            "port": 80,
            "auto_redirect_delay": 3,
            "database": "sqlite:///redirects.db",
            "admin_password": random_pwd,
            "delete_requires_password": True,
            "upstreams": [],
            "log_level": "INFO",  # Default log level (can be changed in config file)
            "redis": {
                "enabled": True,
                "host": redis_default.get("host"),
                "port": redis_default.get("port")
            },
            "upstream_cache": {
                "enabled": True
            }
        }

    def to_dict(self):
        """Expose config for external usage like in templates."""
        return self.cfg


config=Config()