from pydantic import BaseModel, Field, EmailStr, SecretStr, HttpUrl, ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude
from typing import Annotated
from geojson_pydantic import Point


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(
        ..., pattern=r'^^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description='Email пользователя')]
    password: Annotated[SecretStr, Field(
        ..., min_length=8, description='Пароль пользователя(минимум 8 символов)')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    images: Annotated[list[HttpUrl], Field(
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
        ..., pattern=r'^^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description='Email пользователя')]
    password: Annotated[SecretStr, Field(
        ..., min_length=8, description='Пароль пользователя(минимум 8 символов)')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    images: Annotated[list[HttpUrl], Field(
        description='Фотографии пользователя')]
    lon: Longitude
    lat: Latitude
    geo: Point
    model_config = ConfigDict(from_attributes=True)
