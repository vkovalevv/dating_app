from collections.abc import AsyncGenerator
from .database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    with async_session_maker() as session:
        yield session
