from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(BaseModel):
    email: str
    password: str
    username: str

class User(UserBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True 