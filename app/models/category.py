from enum import unique
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    color = Column(String, nullable=True)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    user_id =  Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    __table_args__ = (
        Index("ix_category_user_name", "user_id", "name" , unique=True),
    )