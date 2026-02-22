from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Float


class Preference(Base):
    __tablename__ = 'preferences'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False, unique=True)
    age: Mapped[int] = mapped_column(nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    max_distance: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped['User'] = relationship('User', back_populates='preferences')