from celery import Celery, group
from celery.schedules import crontab
from app.models.users import User as UserModel
from app.database import SessionLocal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB
from app.redis_client import save_stack_to_redis
from geoalchemy2 import WKTElement
from app.config import settings

celery = Celery(
    __name__,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
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
                          .where(UserModel.id == user_id,
                                 UserModel.is_active == True)).first()

        if not user or not user.preferences:
            return

        user_point = ST_GeogFromWKB(user.geo_location)

        stack_ids = db.scalars(
            select(UserModel.id)
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

        if not stack_ids:
            return

        print(stack_ids)
        save_stack_to_redis(user.id, stack_ids)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery.task()
def generate_stack_for_all():
    db = SessionLocal()
    try:
        user_ids = db.scalars(select(UserModel.id)
                              .where(UserModel.is_active == True,
                                     UserModel.preferences.has())).all()
    finally:
        db.close()

    group(generate_stack_for_user.s(usr_id)
          for usr_id in user_ids).apply_async()
