from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        self.connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.connections.pop(user_id, None)

    async def send_personal(self, message: str, to_user_id: int):
        ws = self.connections.get(to_user_id)
        if ws:
            await ws.send_text(message)


manager = ConnectionManager()
