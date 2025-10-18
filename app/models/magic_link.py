
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Boolean , ForeignKey , func
from sqlalchemy.orm import relationship

from app.core.database import Base

class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id" , ondelete="CASCADE"), nullable=False)
    token = Column(String , unique=True, nullable=False , index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="magic_links")