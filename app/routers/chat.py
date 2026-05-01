from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from app.models.users import User as UserModel
from app.models.images import Image
from app.services.auth import get_current_user
from app.services.connection_manager import manager
from app.services.auth import get_user_from_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from sqlalchemy import select, desc, nulls_last, update
from app.models.chat import Conversation, Message
from sqlalchemy import case
from sqlalchemy.orm import aliased, selectinload
from app.schemas.conversations import ConversationOut, MessageOut, Companion
from fastapi_pagination.ext.sqlalchemy import paginate
router = APIRouter(prefix='/chat',
                   tags=['chat'])


def serialize_message(msg: Message) -> dict:
    return {
        'text': msg.text,
        'sender_id': msg.sender_id,
        'created_at': msg.created_at.isoformat(),
        'conversation_id': msg.conversation_id
    }


@router.get('/chat/conversations', response_model=list[ConversationOut])
async def get_conversations(current_user: UserModel = Depends(get_current_user),
                            db: AsyncSession = Depends(get_async_db)):
    message_subquery = (select(Message.conversation_id, Message.text, Message.sender_id, Message.created_at)
                        .distinct(Message.conversation_id)
                        .order_by(Message.conversation_id, desc(Message.created_at))
                        .subquery())
    message_alias = aliased(Message, message_subquery)

    conversations_result = (select(Conversation, UserModel, message_alias.text, message_alias.created_at, message_alias.sender_id)
                            .join(UserModel, UserModel.id == case((Conversation.first_user == current_user.id, Conversation.second_user),
                                                                  else_=Conversation.first_user))
                            .outerjoin(message_alias, Conversation.id == message_alias.conversation_id)
                            .where((Conversation.first_user == current_user.id) | (Conversation.second_user == current_user.id))
                            .order_by(nulls_last(desc(message_alias.created_at)))
                            .options(selectinload(UserModel.images.and_(Image.is_main == True))))
    conversations = (await db.execute(conversations_result)).all()

    result = []
    for row in conversations:
        conversation = row.Conversation
        companion = row.User
        image = companion.images[0].image if companion.images else None

        last_message = None
        if row.text is not None:
            last_message = MessageOut(text=row.text,
                                      created_at=row.created_at,
                                      sender_id=row.sender_id)

        result.append(ConversationOut(conversation_id=conversation.id,
                                      companion=Companion(id=companion.id,
                                                          first_name=companion.first_name,
                                                          img_url=image),
                                      last_message=last_message))
    return result


@router.get('/chat/conversations/{conversation_id}/messages', response_model=list[MessageOut])
async def get_conversation_messages(
        conversation_id: int,
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)):

    conversation = await db.get(Conversation, conversation_id)

    if not conversation or current_user.id not in (conversation.first_user,
                                                   conversation.second_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Conversation not found')

    conversation_messages_result = await db.scalars(select(Message)
                                                    .where(Message.conversation_id == conversation_id)
                                                    .order_by(Message.created_at))
    conversation_messages = conversation_messages_result.all()
    await db.execute(update(Message).where(Message.is_read == False,
                                           Message.conversation_id == conversation_id,
                                           Message.sender_id != current_user.id)
                     .values(is_read=True))
    await db.commit()
    result = []
    for row in conversation_messages:
        sender_id = row.sender_id
        text = row.text
        created_at = row.created_at
        serialize_msg = MessageOut(sender_id=sender_id,
                                   text=text,
                                   created_at=created_at)
        result.append(serialize_msg)
    return result


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
