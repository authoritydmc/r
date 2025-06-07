import os
# --- Redis helpers ---
redis_client = None
redis_enabled = False
redis_host = 'localhost'
redis_port = 6379
running_in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')
from .utils import *