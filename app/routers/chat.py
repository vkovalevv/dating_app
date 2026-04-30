from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.connection_manager import manager
from app.services.auth import get_user_from_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from sqlalchemy import select
from app.models.chat import Conversation, Message
router = APIRouter()


def serialize_message(msg: Message) -> dict:
    return {
        'text': msg.text,
        'from': msg.sender_id,
        'created_at': msg.created_at.isoformat(),
        'conversation_id': msg.conversation_id
    }


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
        message = serialize_message(msg)
        await websocket.send_json(data=message)
        msg.is_read = True

    await db.commit()

    # Listening to WebSocket while the connection is alive
    try:
        while True:
            data = await websocket.receive_json()

            conversation = await db.get(Conversation, data['conversation_id'])
            if not conversation or user.id not in (conversation.first_user,
                                                   conversation.second_user):
                await websocket.send_json({'error': 'conversation not found'})
                continue

            to_user_id = (conversation.first_user if conversation.second_user ==
                          user.id else conversation.second_user)
            message = Message(sender_id=user.id, conversation_id=conversation.id,
                              text=data['text'])

            db.add(message)
            await db.commit()
            await db.refresh(message)
            payload = serialize_message(message)
            await manager.send_personal(payload, to_user_id=to_user_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user.id)
