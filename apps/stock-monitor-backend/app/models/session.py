"""
Session Model
Stores user session data for AI platforms
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Session(Base):
    """Session model for storing platform authentication data"""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String(50), nullable=False, index=True)
    user_id = Column(String(100), nullable=True)
    
    # Authentication data
    cookies = Column(JSON, nullable=True)
    tokens = Column(JSON, nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Session metadata
    metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "platform": self.platform,
            "user_id": self.user_id,
            "cookies": self.cookies,
            "tokens": self.tokens,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
