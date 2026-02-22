from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.preferences import (Preference as PreferenceSchema,
                                     PreferenceCreate)
from app.models.preferences import Preference as PreferenceModel
from app.models.users import User as UserModel
from app.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from sqlalchemy import select, update

router = APIRouter(prefix='/preferences',
                   tags=['preferences'])


@router.post('/create-preference', response_model=PreferenceSchema)
async def create_preference(preference: PreferenceCreate,
                            current_user: UserModel = Depends(
                                get_current_user),
                            db: AsyncSession = Depends(get_async_db)):

    db_preference_result = await db.scalars(
        select(PreferenceModel)
        .where(PreferenceModel.user_id == current_user.id)
    )
    db_preference = db_preference_result.first()

    if db_preference:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='You already posted your preferences.')

    db_preference = PreferenceModel(
        **preference.model_dump(), user_id=current_user.id)

    db.add(db_preference)
    await db.commit()
    await db.refresh(db_preference)
    return db_preference


@router.put('/update-preference', response_model=PreferenceSchema)
async def update_preference(
        preference: PreferenceCreate,
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)):
    db_preference_result = await db.scalars(
        select(PreferenceModel)
        .where(PreferenceModel.user_id == current_user.id)
    )
    db_preference = db_preference_result.first()

    if not db_preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Preference not found.')

    await db.execute(update(PreferenceModel)
                     .where(PreferenceModel.user_id == current_user.id)
                     .values(**preference.model_dump())
                     )
    await db.commit()
    await db.refresh(db_preference)
    return db_preference
