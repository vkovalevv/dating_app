import pytest_asyncio
from app.database import create_async_engine, async_sessionmaker, Base
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import text
from app.db import get_async_db
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.services.auth import hash_password
import os

load_dotenv('.env.test')
TEST_DATABASE_URL = os.getenv('DATABASE_URL')


@pytest_asyncio.fixture()
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(test_db):
    yield
    async with test_db.begin() as conn:
        # reversed() нужен чтобы удалять таблицы в правильном порядке
        # сначала дочерние, потом родительские (из-за foreign keys)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture()
async def async_session(test_db):
    async_session_maker = async_sessionmaker(test_db, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture()
async def async_client(test_db):
    async_session_maker = async_sessionmaker(test_db, expire_on_commit=False)

    async def override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    # подмена зависимости
    app.dependency_overrides[get_async_db] = override_get_async_db

    async with AsyncClient(
        base_url='http://test',
        transport=ASGITransport(app=app)
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def create_user(async_client):
    response = await async_client.post('/users/', json={
        "email": "test@example.com",
        "password": "test11012005",
        "first_name": "Test1",
        "last_name": "Test1",
        "gender": "male",
        "age": 20,
        "role": "user"
        })

    assert response.status_code == 201
    return response.json()