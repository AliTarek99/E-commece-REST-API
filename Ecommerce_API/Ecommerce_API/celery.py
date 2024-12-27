import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ecommerce_API.settings')

app = Celery('Ecommerce_API')

app.conf.broker_url = 'redis://redis:6379'
app.conf.accept_content = ['application/json']
app.conf.task_serializer = 'json'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# app.config_from_object('django.conf:settings')


# Automatically discover tasks in all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')