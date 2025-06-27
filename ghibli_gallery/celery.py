"""
Celery configuration for Ghibli Gallery
Handles background task processing
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ghibli_gallery.settings')

app = Celery('ghibli_gallery')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-failed-artworks': {
        'task': 'gallery.tasks.cleanup_failed_artworks',
        'schedule': 3600.0,  # Run every hour
    },
    'test-api-connection': {
        'task': 'gallery.tasks.test_huggingface_connection',
        'schedule': 1800.0,  # Test connection every 30 minutes
    },
}

app.conf.timezone = 'UTC'

# Task routing and configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=480,  # 8 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')