import pytest
from app.models.users import User
from app.services.auth import hash_password
from app.services.auth import pwd_context
from unittest.mock import patch, MagicMock
from app.services.token import TokenService
from app.services.auth import create_refresh_token


@pytest.mark.asyncio
async def test_login(async_client, create_user):
    with patch('app.routers.users.token_service', spec_set=TokenService) as mock_service:
        mock_service.save_refresh_token = MagicMock()

        response = await async_client.post('/users/token', data={
            'username': "test@example.com",
            'password': 'test11012005'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json()
        assert 'refresh_token' in response.cookies
        assert 'HttpOnly' in response.headers.get('set-cookie', '')


@pytest.mark.asyncio
async def test_refresh_stolen(async_client, create_user):
    # token has been stolen
    with patch('app.routers.users.token_service') as mock_service:
        mock_service.get_user_id.return_value = None
        response = await async_client.post(
            '/users/refresh-token',
            cookies={'refresh_token': create_refresh_token(data={'sub': '42'})})
        assert response.status_code == 401
        mock_service.revoke_all_tokens.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_success(async_client, create_user):
    # casual refreshing
    with patch('app.routers.users.token_service') as mock_service:
        mock_service.get_user_id.return_value = 42
        second_response = await async_client.post(
            '/users/refresh-token',
            cookies={'refresh_token': create_refresh_token(data={'sub': '42'})})
        assert 'access' in second_response.json()
        assert 'refresh_token' in second_response.cookies


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
