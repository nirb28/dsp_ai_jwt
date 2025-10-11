"""
Gunicorn configuration for JWT Service with HTTPS support
"""
import os
import multiprocessing
from dotenv import load_dotenv

load_dotenv()

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5000')}"

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = os.getenv('ACCESS_LOG', 'logs/access.log')
errorlog = os.getenv('ERROR_LOG', 'logs/error.log')
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'jwt-service'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (HTTPS)
ssl_enabled = os.getenv('SSL_ENABLED', 'false').lower() == 'true'
if ssl_enabled:
    certfile = os.getenv('SSL_CERT_FILE', 'certs/server.crt')
    keyfile = os.getenv('SSL_KEY_FILE', 'certs/server.key')
    bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('HTTPS_PORT', '5443')}"
    
    # Verify files exist
    if not os.path.exists(certfile):
        raise FileNotFoundError(f"SSL certificate not found: {certfile}")
    if not os.path.exists(keyfile):
        raise FileNotFoundError(f"SSL key not found: {keyfile}")
