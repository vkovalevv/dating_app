from celery import Celery
from tasks import generate_stack
from celery.schedules import crontab


celery = Celery(
    __name__,
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/1',
    broker_connection_retry_on_startup=True
)

celery.conf.beat_schedule = {
    'background-task': {
        'task': 'tasks.generate_stack',
        'schedule': crontab(hour=4, minute=0), 
        'args': ('Test text message',)
    }
}
