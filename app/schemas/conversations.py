from pydantic import BaseModel
from datetime import datetime


class Companion(BaseModel):
    id: int
    first_name: str
    img_url: str | None = None


class MessageOut(BaseModel):
    id: int 
    conversation_id: int
    sender_id: int
    text: str
    created_at: datetime
    is_read: bool = False

class ConversationOut(BaseModel):
    conversation_id: int
    companion: Companion
    last_message: MessageOut | None = None
