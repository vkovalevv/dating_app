from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from app.database import Base


class Image(Base):
    __tablename__ = 'images'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    image: Mapped[str] = mapped_column(String(200), nullable=False)

    user: Mapped['User'] = relationship(
        'User', back_populates='images', cascade='all, delete-orphan')
