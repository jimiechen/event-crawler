"""
Prompt Model
Stores prompt templates
"""

from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Prompt(Base):
    """Prompt template model"""
    
    __tablename__ = "prompts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    
    # Categorization
    category = Column(String(50), default="general")
    tags = Column(JSON, default=list)
    
    # Template variables (e.g., ["name", "context"])
    variables = Column(JSON, default=list)
    
    # Usage statistics
    usage_count = Column(String(50), default="0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "category": self.category,
            "tags": self.tags or [],
            "variables": self.variables or [],
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def render(self, variables: dict) -> str:
        """Render template with variables"""
        result = self.content
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
