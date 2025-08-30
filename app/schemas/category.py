import uuid

from uuid import UUID
from pydantic import BaseModel , ConfigDict
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)