from sqlalchemy.ext.asyncio import (create_async_engine, async_sessionmaker,
                                    AsyncSession)
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = ('DATABASE_URL=postgresql+asyncpg://datingservice_user:'
                'sergio11012005@localhost:5432/datingservice_db')


async_engine = create_async_engine(DATABASE_URL, echo=True)

asycn_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
