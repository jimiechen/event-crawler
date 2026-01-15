from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete, update
from pydantic import BaseModel
from datetime import datetime, date

from app.config.settings import settings
from app.models.arena_models import PromptTemplate, SignalDefinition, SignalPool
from app.models.ai_decision import AIDecisionResult
from app.database import get_db_session

router = APIRouter(prefix="/arena", tags=["arena"])

# Database Setup
arena_engine = create_async_engine(settings.arena_database_url, echo=False)
AsyncArenaSession = sessionmaker(arena_engine, class_=AsyncSession, expire_on_commit=False)

async def get_arena_db():
    async with AsyncArenaSession() as session:
        yield session

# Pydantic Schemas
class PromptTemplateBase(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    template_text: str
    system_template_text: Optional[str] = None
    is_system: bool = False
    is_deleted: str = "false"
    created_by: str = "system"

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateUpdate(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    template_text: Optional[str] = None
    system_template_text: Optional[str] = None
    is_system: Optional[bool] = None
    is_deleted: Optional[str] = None

class PromptTemplateResponse(PromptTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SignalDefinitionBase(BaseModel):
    signal_name: str
    description: Optional[str] = None
    trigger_condition: Optional[Dict[str, Any]] = None
    enabled: bool = True

class SignalDefinitionCreate(SignalDefinitionBase):
    pass

class SignalDefinitionUpdate(BaseModel):
    signal_name: Optional[str] = None
    description: Optional[str] = None
    trigger_condition: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

class SignalDefinitionResponse(SignalDefinitionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SignalPoolBase(BaseModel):
    pool_name: str
    signal_ids: List[int]
    symbols: List[str] = []
    logic: str = "AND"
    enabled: bool = True

class SignalPoolCreate(SignalPoolBase):
    pass

class SignalPoolUpdate(BaseModel):
    pool_name: Optional[str] = None
    signal_ids: Optional[List[int]] = None
    symbols: Optional[List[str]] = None
    logic: Optional[str] = None
    enabled: Optional[bool] = None

class SignalPoolResponse(SignalPoolBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AIDecisionResponse(BaseModel):
    id: int
    stock_code: str
    trade_date: date
    decision_json: Dict[str, Any]
    model_name: str
    template_name: Optional[str] = None
    primary_operation: Optional[str] = None
    primary_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Routes - Prompts
@router.get("/prompts", response_model=List[PromptTemplateResponse])
async def get_prompts(db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.is_deleted == "false"))
    return result.scalars().all()

@router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt(prompt: PromptTemplateCreate, db: AsyncSession = Depends(get_arena_db)):
    db_prompt = PromptTemplate(**prompt.dict())
    db.add(db_prompt)
    await db.commit()
    await db.refresh(db_prompt)
    return db_prompt

@router.put("/prompts/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(prompt_id: int, prompt: PromptTemplateUpdate, db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
    db_prompt = result.scalar_one_or_none()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    update_data = prompt.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    db_prompt.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_prompt)
    return db_prompt

@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
    db_prompt = result.scalar_one_or_none()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Soft delete
    db_prompt.is_deleted = "true"
    await db.commit()
    return {"message": "Prompt deleted"}

# Routes - Signals
@router.get("/signals", response_model=List[SignalDefinitionResponse])
async def get_signals(db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(SignalDefinition))
    return result.scalars().all()

@router.post("/signals", response_model=SignalDefinitionResponse)
async def create_signal(signal: SignalDefinitionCreate, db: AsyncSession = Depends(get_arena_db)):
    db_signal = SignalDefinition(**signal.dict())
    db.add(db_signal)
    await db.commit()
    await db.refresh(db_signal)
    return db_signal

@router.put("/signals/{signal_id}", response_model=SignalDefinitionResponse)
async def update_signal(signal_id: int, signal: SignalDefinitionUpdate, db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(SignalDefinition).where(SignalDefinition.id == signal_id))
    db_signal = result.scalar_one_or_none()
    if not db_signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    update_data = signal.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_signal, key, value)
        
    await db.commit()
    await db.refresh(db_signal)
    return db_signal

# Routes - Signal Pools
@router.get("/signal-pools", response_model=List[SignalPoolResponse])
async def get_signal_pools(db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(SignalPool))
    return result.scalars().all()

@router.post("/signal-pools", response_model=SignalPoolResponse)
async def create_signal_pool(pool: SignalPoolCreate, db: AsyncSession = Depends(get_arena_db)):
    db_pool = SignalPool(**pool.dict())
    db.add(db_pool)
    await db.commit()
    await db.refresh(db_pool)
    return db_pool

@router.put("/signal-pools/{pool_id}", response_model=SignalPoolResponse)
async def update_signal_pool(pool_id: int, pool: SignalPoolUpdate, db: AsyncSession = Depends(get_arena_db)):
    result = await db.execute(select(SignalPool).where(SignalPool.id == pool_id))
    db_pool = result.scalar_one_or_none()
    if not db_pool:
        raise HTTPException(status_code=404, detail="Signal Pool not found")
    
    update_data = pool.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_pool, key, value)
        
    await db.commit()
    await db.refresh(db_pool)
    return db_pool

# Routes - AI Decisions
@router.get("/decisions", response_model=List[AIDecisionResponse])
async def get_decisions(
    stock_code: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(AIDecisionResult).order_by(AIDecisionResult.created_at.desc())
    if stock_code:
        stmt = stmt.where(AIDecisionResult.stock_code == stock_code)
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()
