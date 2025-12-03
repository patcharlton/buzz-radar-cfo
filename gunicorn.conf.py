# Gunicorn configuration file

# Timeout for worker processes (in seconds)
# Increased from default 30s to handle long-running backfill requests
timeout = 120

# Number of worker processes
workers = 1

# Bind to this address
bind = "0.0.0.0:10000"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
