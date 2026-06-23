import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# Monkeypatch redis-py to default to RESP2 (protocol version 2) globally
# to avoid 'unknown command HELLO' on older Redis servers (like Redis v5 on Windows)
try:
    import redis.connection
    redis.connection.DEFAULT_RESP_VERSION = 2
    
    # Disable maintenance notifications check which fails on RESP2
    if hasattr(redis.connection, 'Connection'):
        redis.connection.Connection._configure_maintenance_notifications = lambda *args, **kwargs: None
    if hasattr(redis.connection, 'AbstractConnection'):
        redis.connection.AbstractConnection._configure_maintenance_notifications = lambda *args, **kwargs: None
except ImportError:
    pass


app = Celery('ecommerce')


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
