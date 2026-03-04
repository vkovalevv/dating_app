import pytest
from app.models.users import User
from app.services.auth import hash_password
from app.services.auth import pwd_context


@pytest.mark.asyncio
async def test_login(async_client, create_user):
    response = await async_client.post('/users/token', data={
        'username': "test@example.com",
        'password': 'test11012005'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.json()


@pytest.mark.asyncio
async def test_wrong_password_login(async_client, create_user):
    response = await async_client.post('/users/token', data={
        'username': "test@example.com",
        'password': 'test11012004'
    })
    assert response.status_code == 401
    assert 'Incorrect email or password' in response.json().values()


@pytest.mark.asyncio
async def test_wrong_password_login(async_client):
    '''
    Проверка логина без авторизации
    '''
    response = await async_client.post('/users/token', data={
        'username': "test2@example.com",
        'password': 'test11012004'
    })
    assert response.status_code == 401
