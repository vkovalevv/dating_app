from app.database import Base
from sqlalchemy import ForeignKey, UniqueConstraint, Boolean, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_user: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False)
    second_user: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('first_user', 'second_user'),
    )


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey('conversations.id'), nullable=False)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
