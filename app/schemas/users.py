from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict,    field_validator
from pydantic_extra_types.coordinate import Latitude, Longitude
from typing import Annotated
from .images import Image as ImageSchema
from geoalchemy2.shape import to_shape

class Coordinates(BaseModel):
    latitude: Latitude
    longitude: Longitude


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(
        ...,
        description='Email пользователя')]
    password: Annotated[str, Field(
        ..., min_length=8, description='Пароль пользователя(минимум 8 символов)')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    gender: Annotated[str, Field(..., pattern='^(male|female)$',
                                 description='Пол пользователя.')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    role: Annotated[str, Field(
        default='user', pattern='^(user|admin)$', description='Роль: user или admin')]
    images: Annotated[list[str], Field(default_factory=list,
                                       description='Фотографии пользователя')]


class UserInfoUpdate(BaseModel):
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    age: Annotated[int, Field(ge=18, description='Возраст пользователя')]
    gender: Annotated[str, Field(
        pattern='^(male|female)$', description='Пол пользователя.')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None


class User(BaseModel):
    id: int
    email: Annotated[EmailStr, Field(
        ..., description='Email пользователя')]
    first_name: Annotated[str,
                          Field(..., min_length=2, description='Имя пользователя')]
    last_name: Annotated[str, Field(..., description='Фамилия пользователя')]
    gender: Annotated[str, Field(..., pattern='^(male|female)$',
                                 description='Пол пользователя.')]
    age: Annotated[int, Field(..., ge=18, description='Возраст пользователя')]
    description: Annotated[str | None, Field(
        max_length=250, description='Описание профиля пользователя')] = None
    images: Annotated[list[ImageSchema], Field(
        description='Фотографии пользователя')]
    longitude: Longitude | None = None
    latitude: Latitude | None = None
    geo_location: Annotated[str | None, Field(
        exclude=True, default=None)] = None
    is_active: bool
    role: Annotated[str, Field(pattern='^(user|admin)$')]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("geo_location", mode="before")
    def turn_geo_location_into_wkt(cls, value):
        return to_shape(value).wkt
    


class UsersStack(BaseModel):

    users: list[User]
    model_config = ConfigDict(from_attributes=True)
