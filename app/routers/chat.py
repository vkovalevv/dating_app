from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.connection_manager import manager
from app.services.auth import get_user_from_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
router = APIRouter()


@router.websocket('/ws')
async def chat_endpoint(websocket: WebSocket,
                        db: AsyncSession = Depends(get_async_db)) -> None:
    await websocket.accept()

    auth_data = await websocket.receive_json()
    user = await get_user_from_token(auth_data.get('token'), db)

    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)

    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_personal(data['text'], to_user_id=data['to'])
    except WebSocketDisconnect:
        manager.disconnect(user.id)
