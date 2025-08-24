from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    original_message = Column(Text, nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")