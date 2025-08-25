# app/schemas/user.py
import uuid
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    phone_number: str
    name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True