from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_text = Column(Text, nullable=False)
    system_template_text = Column(Text)
    is_system = Column(Boolean, default=False)
    is_deleted = Column(String(10), default="false") # 'true' or 'false'
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SignalDefinition(Base):
    __tablename__ = "signal_definitions"

    id = Column(Integer, primary_key=True, index=True)
    signal_name = Column(String(255), nullable=False) # Changed from name to signal_name based on adapter query
    description = Column(Text)
    # signal_type = Column(String(50), nullable=False) # Removed as it doesn't exist in remote DB
    trigger_condition = Column(JSON) # e.g., {"indicator": "MA", "operator": ">", "value": 0}
    # parameters = Column(JSON) # e.g., {"window": 5}
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SignalPool(Base):
    __tablename__ = "signal_pools"

    id = Column(Integer, primary_key=True, index=True)
    pool_name = Column(String(255), unique=True, nullable=False)
    # description = Column(Text) # Removed as it doesn't exist in remote DB
    signal_ids = Column(JSON) # List of SignalDefinition IDs
    symbols = Column(JSON, default=[]) # List of symbols to apply
    logic = Column(String(10), default="AND") # 'AND' or 'OR'
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
