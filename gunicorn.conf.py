# gunicorn.conf.py

# Number of worker processes (adjust based on CPU cores)
workers = 4

# Threads per worker (useful for I/O-heavy tasks)
threads = 4

# The host and port to bind to
bind = "0.0.0.0:80"

# Worker timeout in seconds
timeout = 60

# Whether to preload the app before forking (saves memory, faster startup)
preload_app = True

# Log levels: debug, info, warning, error, critical
loglevel = "info"

# Log to stdout/stderr
accesslog = "-"
errorlog = "-"

# Enable auto-restart on code changes (use only in dev)
reload = False
