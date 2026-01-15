#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Decision Controller
Provides API endpoints for generating AI trading decisions.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database import get_db_session
from ..config.settings import get_settings
from ..services.ai_decision_service import AIDecisionService, AIDecisionConfig
from ..config.prompt_templates import STOCK_DEFAULT_PROMPT_TEMPLATE

router = APIRouter(prefix="/api/v1/decision", tags=["AI决策"])

class DecisionRequest(BaseModel):
    stock_code: str
    template_text: Optional[str] = None
    model: Optional[str] = None

class ContextResponse(BaseModel):
    stock_code: str
    context: Dict[str, Any]

class DecisionResponse(BaseModel):
    stock_code: str
    decision: Dict[str, Any]
    timestamp: str

def get_ai_service() -> AIDecisionService:
    settings = get_settings()
    config = AIDecisionConfig(
        api_key=settings.deepseek_api_key or "",
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model
    )
    return AIDecisionService(config)

@router.post("/context/{stock_code}", response_model=ContextResponse, summary="获取决策上下文")
async def get_decision_context(
    stock_code: str,
    template_text: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the context data used for AI decision making.
    Useful for debugging prompts and data availability.
    """
    service = get_ai_service()
    template = template_text or STOCK_DEFAULT_PROMPT_TEMPLATE
    
    try:
        context = await service.prepare_decision_context(db, stock_code, template)
        return ContextResponse(
            stock_code=stock_code,
            context=context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{stock_code}", response_model=DecisionResponse, summary="生成AI决策")
async def generate_decision(
    stock_code: str,
    request: DecisionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a trading decision using AI.
    """
    service = get_ai_service()
    if not service.config.api_key:
        raise HTTPException(status_code=500, detail="DeepSeek API Key not configured")
        
    template = request.template_text or STOCK_DEFAULT_PROMPT_TEMPLATE
    
    try:
        result = await service.generate_decision(
            session=db,
            stock_code=stock_code,
            template_text=template,
            model=request.model
        )
        
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
             
        return DecisionResponse(
            stock_code=stock_code,
            decision=result,
            timestamp=result.get("timestamp", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
