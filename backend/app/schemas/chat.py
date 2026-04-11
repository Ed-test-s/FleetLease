from datetime import datetime

from pydantic import BaseModel

from app.models.chat import ChatType


class ChatCreate(BaseModel):
    chat_type: ChatType
    request_id: int | None = None
    contract_id: int | None = None
    participant_ids: list[int]


class ChatParticipantOut(BaseModel):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    message_text: str
    file_url: str | None = None


class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    message_text: str
    file_url: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatOut(BaseModel):
    id: int
    chat_type: ChatType
    request_id: int | None = None
    contract_id: int | None = None
    created_at: datetime
    participants: list[ChatParticipantOut] = []
    last_message: MessageOut | None = None
    model_config = {"from_attributes": True}
