# gunicorn.conf.py

# Number of worker processes (adjust based on CPU cores)
# For gevent, workers usually correspond to CPU cores.
# Each gevent worker can handle many concurrent connections.
workers = 4

# Specify the worker class as gevent
# This is the key change to use gevent for asynchronous I/O
worker_class = "gevent"

# For gevent, threads are typically not used in the same way as sync workers.
# gevent workers are single-threaded but use greenlets for concurrency.
# You can remove 'threads' or set it to 1 if you explicitly want to constrain to one OS thread per worker.
# Leaving it can sometimes cause unexpected behavior if gevent doesn't fully bypass Gunicorn's threading model.
# Best practice with gevent is often to omit 'threads' or set it to 1.
# threads = 1 # Recommended if you include it, otherwise omit

# The host and port to bind to
bind = "0.0.0.0:80"

# Worker timeout in seconds
# Gevent workers handle concurrent requests without blocking, so timeouts can often be higher.
# However, if you have long-running external calls, ensure this is enough.
timeout = 60

# Whether to preload the app before forking (saves memory, faster startup)
preload_app = True

# Log levels: debug, info, warning, error, critical
loglevel = "info"

# Log to stdout/stderr
accesslog = "-"
errorlog = "-"

# Enable auto-restart on code changes (use only in dev)
# Make sure to disable this in production for stability
reload = False