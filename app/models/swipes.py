from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Boolean, Integer
from typing import Annotated
from enum import Enum

class SwipeAction(Enum):
    PASS = 0
    LIKE = 1

class Swipe(Base):
    __tablename__ = 'swipes'

    first_user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), primary_key=True, nullable=False)
    second_user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), primary_key=True, nullable=False)
    first_action: Mapped[int] = mapped_column(Integer, nullable=False)
    second_action: Mapped[int] = mapped_column(Integer, nullable=True)
