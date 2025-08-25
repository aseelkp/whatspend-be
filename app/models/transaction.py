
import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Enum, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    amount = Column(Float, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)

    raw_message = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)


    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")