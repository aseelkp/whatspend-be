import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Enum, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionType(enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    amount = Column(Float, nullable=False)
    transaction_type = Column(
        Enum(TransactionType, name="transaction_type", create_type=True), nullable=False
    )
    description = Column(String(255), nullable=True)
    raw_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
