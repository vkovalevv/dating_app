from pydantic import BaseModel
from datetime import datetime


class Companion(BaseModel):
    id: int
    first_name: str
    img_url: str | None = None


class MessageOut(BaseModel):
    sender_id: int
    text: str
    created_at: datetime

class ConversationOut(BaseModel):
    conversation_id: int
    companion: Companion
    last_message: MessageOut | None = None
