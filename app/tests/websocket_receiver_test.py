import asyncio
import websockets
import json
import httpx
from dotenv import load_dotenv
import os

load_dotenv()


async def test_receiver():
    RECEIVER_USERNAME = os.getenv('RECEIVER_USERNAME')
    RECEIVER_PASSWORD = os.getenv('RECEIVER_PASSWORD')
    async with httpx.AsyncClient() as client:
        response = await client.post('http://localhost:8000/users/token',
                                     data={'username': f'{RECEIVER_USERNAME}',
                                           'password': f'{RECEIVER_PASSWORD}'})
        token = response.json()['access_token']

    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # авторизация
        await ws.send(json.dumps({"token": token}))
        print("токен отправлен")

        print("подключился, жду сообщений...")
        while True:
            message = await ws.recv()
            print(f"получил: {message}")

asyncio.run(test_receiver())
