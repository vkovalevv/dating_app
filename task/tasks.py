from fastapi import Depends
from celery import shared_task
from celery.exceptions
from app.models.preferences import Preference as PreferenceModel
from app.models.users import User as UserModel
from app.database import SessionLocal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DWithin


@shared_task
async def generate_stack():
    db = SessionLocal()
    try:
        users = db.scalars(select(UserModel)
                           .options(selectinload(UserModel.preferences))
                           .where(UserModel.is_active)
                           ).all()
        for user in users:
            stack = db.scalars(
                select(UserModel)
                .where(UserModel.is_active==True, UserModel.id!=user.id)
                .where(ST_DWithin(UserModel.geo_location, user.geo_location,user.preferences.max_distance))
                .where(UserModel.gender == user.preferences.gender,
                       UserModel.age >= user.preferences.age)).all()
    except Exception as e:
        print(e)
        raise e
    finally:
        db.close()
