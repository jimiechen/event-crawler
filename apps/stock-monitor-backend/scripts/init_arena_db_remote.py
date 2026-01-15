import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.declarative import declarative_base

# Add Arena backend to path to import models
arena_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Hyper-Alpha-Arena-main/backend"))
sys.path.append(arena_backend_path)

try:
    from database.models import Base
    # Import all models to ensure they are registered with Base
    from database.models import (
        User, Account, Position, Order, Trade, PromptTemplate, 
        SignalDefinition, SignalPool, AIDecisionLog
    )
    print("Successfully imported models from Arena backend.")
except ImportError as e:
    print(f"Error importing models: {e}")
    sys.exit(1)

# Connection string for 192.168.1.6
DB_URL = "postgresql+psycopg2://chroma_user:chroma_password@192.168.1.6:5432/chroma_db"

def init_db():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_engine(DB_URL)
        print("Connected. Creating tables...")
        
        # Create all tables defined in Base
        Base.metadata.create_all(engine)
        
        print("All tables created successfully!")
        
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
