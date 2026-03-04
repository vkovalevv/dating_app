import pytest_asyncio
from app.database import Base
from app.database import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os

load_dotenv('.env.test')
TEST_DATABASE_URL = os.getenv('DATABASE_URL')


@pytest_asyncio.fixture(scope='session')
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(test_db):
    yield
    async with test_db.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture()
async def async_session(test_db):
    async_session_maker = async_sessionmaker(test_db, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
