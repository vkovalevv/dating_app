from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude
from typing import Annotated
from geojson_pydantic import Point
from .images import Image as ImageSchema

class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(
        ...,
        description='Email пользователя')]
    password: Annotated[str, Field(
        ..., min_length=8, description='Пароль пользователя(минимум 8 символов)')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    role: Annotated[str, Field(
        default='user', pattern='^(user|admin)$', description='Роль: user или admin')]
    images: Annotated[list[str], Field(default_factory=list,
        description='Фотографии пользователя')]


class UserUpdate(BaseModel):
    age: Annotated[int, Field(ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    images: Annotated[list[HttpUrl], Field(
        description='Фотографии пользователя')]


class User(BaseModel):
    id: int
    email: Annotated[EmailStr, Field(
        ..., description='Email пользователя')]
    password: Annotated[str, Field(
        ..., min_length=8, description='Пароль пользователя(минимум 8 символов)')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    images: Annotated[list[ImageSchema], Field(
        description='Фотографии пользователя')]
    lon: Longitude | None = None
    lat: Latitude | None = None
    geo: Point | None = None
    is_active: bool
    role: Annotated[str, Field(pattern='^(user|admin)$')]

    model_config = ConfigDict(from_attributes=True)
