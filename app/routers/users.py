from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.users import (UserCreate, User as UserSchema, Coordinates,
                               UserInfoUpdate, RefreshSchema)

from app.schemas.preferences import Preference as PreferenceSchema

from app.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import User as UserModel, Image as ImageModel
from app.services.auth import (verify_password, create_refresh_token,
                               create_access_token, hash_password, get_current_user)
from fastapi.security import OAuth2PasswordRequestForm
from geoalchemy2.functions import ST_GeogFromText

import jwt
from fastapi import UploadFile
from app.schemas.images import Image as ImageSchema
from app.config import settings
from app.redis_client import redis_tokens

from app.services.images import save_user_image

router = APIRouter(prefix='/users',
                   tags=['users'])


@router.get('/me/preferences', response_model=PreferenceSchema)
async def get_preferences(current_user: UserModel = Depends(get_current_user)):
    if not current_user.preferences:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User has no preferences')
    return current_user.preferences

@router.post('/', response_model=UserSchema, status_code=201)
async def create_user(user: UserCreate,
                      db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(UserModel)
                              .where(UserModel.email == user.email,
                                     UserModel.is_active == True)
                              .options(selectinload(UserModel.images)))
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Email already registered')

    db_user = UserModel(email=user.email,
                        password=hash_password(user.password),
                        first_name=user.first_name,
                        last_name=user.last_name,
                        gender=user.gender,
                        age=user.age,
                        description=user.description,
                        role=user.role
                        )
    db.add(db_user)
    await db.commit()
    db_user = (await db.scalars(select(UserModel)
                                .where(UserModel.email == user.email,
                                       UserModel.is_active == True)
                                .options(selectinload(UserModel.images)))
               ).first()
    return db_user


@router.post('/images', response_model=list[ImageSchema])
async def upload_user_images(
        images: list[UploadFile],
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)):

    for i, image in enumerate(images):
        image_url = await save_user_image(image)
        img = ImageModel(user_id=current_user.id,
                         image=image_url,
                         order=i,
                         is_main=(i == 0))
        db.add(img)
    await db.commit()
    images = (await db.scalars(select(ImageModel)
                               .where(ImageModel.user_id == current_user.id))
              ).all()
    return images


@router.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_db)):
    user = (await db.scalars(select(UserModel)
                             .where(UserModel.email == form_data.username,
                                    UserModel.is_active == True)
                             )).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'})

    access_token = create_access_token(
        data={"sub": str(user.id)})
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)})

    redis_tokens.setex(f'refresh:{user.id}', 60*60*24*30, refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post('/refresh-token')
async def refresh(data: RefreshSchema, db: AsyncSession = Depends(get_async_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token has expired.',
        headers={
            'WWW-Authenticate': 'Bearer'
        })
    try:
        payload = jwt.decode(data.refresh_token,
                             key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload['sub'])
    except jwt.PyJWTError:
        raise credentials_exception

    stored = redis_tokens.get(f'refresh:{user_id}')

    if not stored or stored != data.refresh_token:
        raise credentials_exception

    new_access_token = create_access_token(data={'sub': str(user_id)})
    new_refresh_token = create_refresh_token(data={'sub': str(user_id)})

    redis_tokens.setex(f'refresh:{user_id}',
                       60*60*24*30,
                       new_refresh_token)

    return {'access': new_access_token,
            'refresh': new_refresh_token}


@router.put('/update-location', response_model=UserSchema)
async def uptade_location(coordinates: Coordinates,
                          current_user: UserModel = Depends(get_current_user),
                          db: AsyncSession = Depends(get_async_db)):
    current_user.latitude = coordinates.latitude
    current_user.longitude = coordinates.longitude

    current_user.geo_location = ST_GeogFromText(
        f'POINT({current_user.longitude} {current_user.latitude})',
        srid=4326
    )
    await db.commit()
    await db.refresh(current_user)
    result = await db.scalars(select(UserModel)
                              .where(UserModel.id == current_user.id)
                              .options(selectinload(UserModel.images))
                              )

    result_user = result.first()

    return result_user


@router.delete('/{user_id}/profile/delete')
async def delete_user(user_id: int,
                      db: AsyncSession = Depends(get_async_db),
                      current_user: UserModel = Depends(get_current_user)):

    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Only author or admins can perform this action.')

    result = await db.scalars(select(UserModel)
                              .where(UserModel.id == user_id,
                                     UserModel.is_active == True))
    db_user = result.first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')

    await db.execute(update(UserModel)
                     .where(UserModel.id == user_id)
                     .values(is_active=False))
    await db.commit()
    await db.refresh(db_user)

    return {'message': 'User deleted.'}


@router.put('/{user_id}/profile/update', response_model=UserSchema)
async def update_user_info(user_id: int,
                           payload: UserInfoUpdate,
                           db: AsyncSession = Depends(get_async_db),
                           current_user: UserModel = Depends(get_current_user)):

    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Only author or admins can perform this action.')

    result = await db.scalars(select(UserModel)
                              .where(UserModel.is_active == True,
                                     UserModel.id == user_id))
    db_user = result.first()

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')

    await db.execute(update(UserModel)
                     .where(UserModel.id == user_id)
                     .values(**payload.model_dump(exclude_unset=True)))
    await db.commit()
    await db.refresh(db_user)

    db_user = await db.scalars(select(UserModel)
                               .where(UserModel.id == user_id,
                                      UserModel.is_active == True)
                               .options(selectinload(UserModel.images)))

    db_user_result = db_user.first()
    return db_user_result
