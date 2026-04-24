from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.users import (UserCreate, User as UserSchema, Coordinates,
                               UserInfoUpdate, RefreshSchema, UserProfile, UserInfoPartlyUpdate)

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
from fastapi import UploadFile, Response, Request
from app.schemas.images import Image as ImageSchema
from app.config import settings
from app.services.token import token_service, REFRESH_TOKEN_TTL

from app.services.images import save_user_image
from app.limiter import limiter

router = APIRouter(prefix='/users',
                   tags=['users'])


@router.get('/me/preferences', response_model=PreferenceSchema)
async def get_preferences(current_user: UserModel = Depends(get_current_user)):
    if not current_user.preferences:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User has no preferences')
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
@limiter.limit('10/minute')
async def login(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
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

    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=REFRESH_TOKEN_TTL,
        samesite='lax',
        httponly=True
    )
    token_service.save_refresh_token(user_id=user.id, token=refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/logout')
async def logout(response: Response,
                 request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token has expired.',
        headers={
            'WWW-Authenticate': 'Bearer'
        })

    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(refresh_token,
                             key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = int(payload['sub'])
    except jwt.PyJWTError:
        raise credentials_exception

    response.delete_cookie('refresh_token')
    token_service.revoke_token(user_id=user, token=refresh_token)
    return {'message': 'success'}


@router.post('/refresh-token')
@limiter.limit('5/minute')
async def refresh(
        response: Response,
        request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token has expired.',
        headers={
            'WWW-Authenticate': 'Bearer'
        })

    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(refresh_token,
                             key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = int(payload['sub'])
    except jwt.PyJWTError:
        raise credentials_exception

    user_id = token_service.get_user_id(refresh_token)
    if not user_id:
        # token has been stolen
        token_service.revoke_all_tokens(user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        new_access_token = create_access_token(data={'sub': str(user_id)})
        new_refresh_token = create_refresh_token(data={'sub': str(user_id)})
        token_service.rotate_refresh_token(
            user_id, refresh_token, new_refresh_token)
        response.set_cookie(
            key='refresh_token',
            value=new_refresh_token,
            max_age=REFRESH_TOKEN_TTL,
            httponly=True,
            samesite='lax'
        )
    return {'access': new_access_token}


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


@router.patch('/me/update-info', response_model=UserSchema)
async def partly_update_user(payload: UserInfoPartlyUpdate,
                             current_user: UserModel = Depends(
                                 get_current_user),
                             db: AsyncSession = Depends(get_async_db)):
    await db.execute(update(UserModel)
                     .where(UserModel.id == current_user.id)
                     .values(**payload.model_dump(exclude_unset=True)))
    await db.commit()

    db_user_result = await db.scalars(select(UserModel)
                                      .where(UserModel.id == current_user.id,
                                             UserModel.is_active == True)
                                      .options(selectinload(UserModel.images)))
    db_user = db_user_result.first()
    return db_user


@router.get('/me', response_model=UserProfile)
async def get_current_profile(current_user: UserModel = Depends(get_current_user),
                              db: AsyncSession = Depends(get_async_db)):
    user_result = await db.scalars(select(UserModel)
                                   .where(UserModel.id == current_user.id)
                                   .options(selectinload(UserModel.images)))
    user = user_result.first()
    return user
