from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TransactionBase(BaseModel):
    amount: float
    description: str
    category_id: Optional[int] = None
    transaction_date: datetime

class TransactionCreate(TransactionBase):
    original_message: Optional[str] = None

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    transaction_date: Optional[datetime] = None

class TransactionInDB(TransactionBase):
    id: int
    user_id: int
    original_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Transaction(TransactionInDB):
    pass