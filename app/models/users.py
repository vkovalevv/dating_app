from app.database import Base
from sqlalchemy import Integer, String, Text, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography, WKBElement


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(
        String, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 8), nullable=True, default=None)
    longitude: Mapped[float | None] = mapped_column(
        Numeric(11, 8), nullable=True, default=None)
    geo_location: Mapped[WKBElement | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[bool] = mapped_column(String, default='user', nullable=False)

    images: Mapped[list['Image']] = relationship(
        'Image', back_populates='user')
