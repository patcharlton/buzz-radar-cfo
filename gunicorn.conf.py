# Gunicorn configuration file
# Optimized for Render Starter plan (512MB RAM)

# Timeout for worker processes (in seconds)
# Increased from default 30s to handle long-running AI/backfill requests
timeout = 120

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Number of worker processes
# 2 workers optimal for 512MB RAM with threaded I/O
workers = 2

# Threads per worker for better concurrency on I/O-bound operations
threads = 2
worker_class = "gthread"

# Bind to this address
bind = "0.0.0.0:10000"

# Keep-alive connections
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload app for memory efficiency (shares code between workers)
preload_app = True

# Worker recycling to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50
