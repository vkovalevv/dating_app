from sqlalchemy.ext.asyncio import (create_async_engine, async_sessionmaker,
                                    AsyncSession)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = 'postgresql+asyncpg://datingservice_user:sergio11012005@localhost:5432/datingservice_db'


async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession)


# Отдельный синхронный движок для Celery
sync_engine = create_engine(DATABASE_URL.replace("+asyncpg", "+psycopg2"))
SessionLocal = sessionmaker(bind=sync_engine)

class Base(DeclarativeBase):
    pass
