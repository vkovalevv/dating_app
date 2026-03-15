from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.connection_manager import manager
from app.services.auth import get_user_from_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from sqlalchemy import select
from app.models.chat import Conversation, Message
router = APIRouter()


@router.websocket('/ws')
async def chat_endpoint(websocket: WebSocket,
                        db: AsyncSession = Depends(get_async_db)) -> None:
    await websocket.accept()

    # The first WebSocket message is for token verification
    auth_data = await websocket.receive_json()
    user = await get_user_from_token(auth_data.get('token'), db)

    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)

    # Extract from the DB messages that were received while the user was offline
    unread = await db.scalars(
        select(Message)
        .where(
            Message.conversation_id.in_(
                select(Conversation.id)
                .where((Conversation.first_user == user.id) |
                       (Conversation.second_user == user.id))
            ),
            Message.sender_id != user.id,
            Message.is_read == False
        )
        .order_by(Message.created_at)
    )
    unread_messages = unread.all()

    for msg in unread_messages:
        await websocket.send_json({'from': msg.sender_id,
                                  'text': msg.text,
                                  'created_at': msg.created_at.isoformat()})
        print(msg.text)
        msg.is_read = True

    await db.commit()

    # Listening to WebSocket while the connection is alive
    try:
        while True:
            data = await websocket.receive_json()

            first_user, second_user = sorted([user.id, data['to']])

            conversation_result = await db.scalars(select(Conversation)
                                                   .where(Conversation.first_user == first_user,
                                                          Conversation.second_user == second_user))

            conversation = conversation_result.first()
            if not conversation:
                await websocket.send_json({'error': 'conversation not found'})
                continue

            message = Message(sender_id=user.id, conversation_id=conversation.id,
                              text=data['text'])
            db.add(message)
            await db.commit()

            await manager.send_personal(data['text'], to_user_id=data['to'])
    except WebSocketDisconnect:
        manager.disconnect(user.id)
