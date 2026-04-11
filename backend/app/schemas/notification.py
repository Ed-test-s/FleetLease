from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    text: str


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    text: str
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
