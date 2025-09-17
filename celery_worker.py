import os
from outreach_pilot import create_app
from outreach_pilot.tasks import celery

# Use the app factory to create a Flask app instance
app = create_app()

# Update Celery configuration
celery.conf.update(
    # This new line fixes the deprecation warning
    broker_connection_retry_on_startup=True,
    
    # Using JSON as a best practice for serializers
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)

# This ensures tasks have access to the Flask application context
TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask
