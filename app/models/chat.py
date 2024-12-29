from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    id: Optional[uuid.UUID] = None
    user_id: str
    content: str
    role: str
    created_at: Optional[datetime] = None
    conversation_id: Optional[str] = None

    @field_serializer('created_at')
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if d.get('created_at') and isinstance(d['created_at'], datetime):
            d['created_at'] = d['created_at'].isoformat()
        return d

    class Config:
        from_attributes = True