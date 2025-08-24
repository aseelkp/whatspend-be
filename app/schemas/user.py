from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    phone_number: str
    name: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDB):
    pass