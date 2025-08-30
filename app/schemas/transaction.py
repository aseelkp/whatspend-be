from pydantic import BaseModel , validator , ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionType(str , Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class TransactionBase(BaseModel):
    amount : Decimal
    transaction_type: TransactionType
    category_id : str
    description: str
    raw_message: Optional[str] = None

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

class TransactionCreate(TransactionBase):
    user_id: str
class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    raw_message: Optional[str] = None
    transaction_type: Optional[TransactionType] = None

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v

class TransactionResponse(TransactionBase):
    id : str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    category_name : str
    category_display_name : str
    category_icon : Optional[str] = None


    model_config = ConfigDict(from_attributes=True)

class TransactionFilter(BaseModel):
    user_id: Optional[str] = None
    category_id: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None