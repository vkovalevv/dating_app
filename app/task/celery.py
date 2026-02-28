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
)

celery.conf.beat_schedule = {
    'background-task': {
        'task': 'app.task.generate_stack_for_all',
        'schedule': crontab(hour=3, minute=0)
    }
}


@celery.task(bind=True, max_retries=3)
def generate_stack_for_user(self, user_id: int):
    db = SessionLocal()
    try:
        user = db.scalars(select(UserModel)
                          .options(selectinload(UserModel.preferences))
                          .where(UserModel.id == user_id)).first()

        if not user or not user.preferences:
            return

        user_point = ST_GeogFromWKB(user.geo_location)

        stack = db.scalars(
            select(UserModel)
            .where(
                UserModel.is_active == True,
                UserModel.id != user.id,
                UserModel.gender == user.preferences.gender,
                UserModel.age >= user.preferences.age,
                ST_DWithin(
                    UserModel.geo_location,
                    user_point,
                    user.preferences.max_distance*1000
                )
            )).all()
        save_stack_to_redis(user, stack)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery.task()
def generate_stack_for_all():
    db = SessionLocal()
    try:
        users = db.scalars(select(UserModel.id)
                           .where(UserModel.is_active == True,
                                  UserModel.preferences.has())).all()
        for user_id in users:
            generate_stack_for_user.apply_async([user_id])
    finally:
        db.close()
