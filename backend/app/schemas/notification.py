from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    text: str
    type: str | None = None
    entity_id: int | None = None


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    text: str
    type: str | None = None
    entity_id: int | None = None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
