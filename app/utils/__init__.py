import os
import logging

logger = logging.getLogger("UTILS_INITIALISING")

# --- Redis helpers ---
redis_client = None
redis_enabled = False

# Get Redis settings from environment variables with defaults
redis_port = int(os.getenv('REDIS_PORT', 6379))  # Convert to int, default to 6379

# Detect if running inside Docker
running_in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') is not None
redis_host = os.getenv('REDIS_HOST', 'redis' if running_in_docker else 'localhost')  # Use env var or default to 'localhost'


logger.info(f"Redis Host: {redis_host}, Port: {redis_port}, Running in Docker: {running_in_docker}")
