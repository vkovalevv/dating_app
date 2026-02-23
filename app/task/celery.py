from celery import Celery
from celery.schedules import crontab
from app.models.users import User as UserModel
from app.database import SessionLocal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB
from app.redis import save_stack_to_redis, get_stack_from_redis
from geoalchemy2 import WKTElement
celery = Celery(
    __name__,
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/1',
    broker_connection_retry_on_startup=True,
    include=['app.task.celery']
)

celery.conf.beat_schedule = {
    'background-task': {
        'task': 'generate_stack',
        'schedule': crontab(hour=4, minute=0)
    }
}


@celery.task()
def generate_stack():
    db = SessionLocal()

    try:
        users = db.scalars(select(UserModel)
                           .options(selectinload(UserModel.preferences))
                           .where(UserModel.is_active)
                           .execution_options(yield_per=100))
        for user in users:
            if not user.preferences:
                continue

            user_point = ST_GeogFromWKB(user.geo_location)

            stack = db.scalars(
                select(UserModel)
                .options(selectinload(UserModel.images))
                .where(UserModel.is_active == True, UserModel.id != user.id)
                .where(ST_DWithin(UserModel.geo_location, user_point, user.preferences.max_distance*1000))
                .where(UserModel.gender == user.preferences.gender,
                       UserModel.age >= user.preferences.age)).all()
            save_stack_to_redis(user, stack)
    except Exception as e:
        print(e)
        raise e
    finally:
        db.close()
