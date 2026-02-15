from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.users import UserCreate, User as UserSchema

from app.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User as UserModel
from app.auth import verify_password, create_refresh_token, create_access_token, hash_password
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix='/users',
                   tags=['users'])


@router.post('/', response_model=UserSchema, status_code=201)
async def create_user(user: UserCreate,
                      db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(UserModel).where(UserModel.email == user.email,
                                                      UserModel.is_active == True))
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Email already registered')

    db_user = UserModel(email=user.email,
                        password=hash_password(user.password),
                        first_name=user.first_name,
                        last_name=user.last_name,
                        age=user.age,
                        description=user.description,
                        role=user.role
                        )
    db.add(db_user)
    await db.commit()
    return db_user


@router.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_db)):
    user = (await db.scalars(select(UserModel)
                             .where(UserModel.email == form_data.username,
                                    UserModel.is_active == True)
                             )).first
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'})

    access_token = create_access_token(
        data={"sub": user.email, "id": user.id})
    refresh_token = create_refresh_token(
        data={"sub": user.email, "id": user.id})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
