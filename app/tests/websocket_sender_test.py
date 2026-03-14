import asyncio
import websockets
import json
import httpx

from dotenv import load_dotenv
import os

load_dotenv()


async def test_sender():
    SENDER_USERNAME = os.getenv('SENDER_USERNAME')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    async with httpx.AsyncClient() as client:
        response = await client.post('http://localhost:8000/users/token',
                                     data={'username': f'{SENDER_USERNAME}',
                                           'password': f'{SENDER_PASSWORD}'})
        token = response.json()['access_token']

    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # авторизация
        await ws.send(json.dumps({"token": token}))
        print("токен отправлен")

        # отправка сообщения
        await ws.send(json.dumps({"to": 19, "text": "привет"}))
        print("сообщение отправлено")

        await asyncio.sleep(2)

asyncio.run(test_sender())
