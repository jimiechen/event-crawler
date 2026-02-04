"""
Prompt Management API
Handles prompt templates storage and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db_session
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptData(BaseModel):
    """Prompt data model"""
    name: str
    content: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = "general"
    variables: Optional[List[str]] = []


class PromptUpdate(BaseModel):
    """Prompt update model"""
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    variables: Optional[List[str]] = None


@router.post("/")
async def create_prompt(
    data: PromptData,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new prompt template"""
    try:
        service = PromptService(db)
        prompt = await service.create_prompt(
            name=data.name,
            content=data.content,
            description=data.description,
            tags=data.tags,
            category=data.category,
            variables=data.variables
        )
        return {
            "success": True,
            "prompt": {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "tags": prompt.tags,
                "category": prompt.category,
                "created_at": prompt.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a prompt template by ID"""
    try:
        service = PromptService(db)
        prompt = await service.get_prompt(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return {
            "success": True,
            "prompt": {
                "id": prompt.id,
                "name": prompt.name,
                "content": prompt.content,
                "description": prompt.description,
                "tags": prompt.tags,
                "category": prompt.category,
                "variables": prompt.variables,
                "created_at": prompt.created_at,
                "updated_at": prompt.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-name/{name}")
async def get_prompt_by_name(
    name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a prompt template by name"""
    try:
        service = PromptService(db)
        prompt = await service.get_prompt_by_name(name)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt not found: {name}")
        
        return {
            "success": True,
            "prompt": {
                "id": prompt.id,
                "name": prompt.name,
                "content": prompt.content,
                "description": prompt.description,
                "tags": prompt.tags,
                "category": prompt.category,
                "variables": prompt.variables
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_prompts(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List prompt templates with optional filtering"""
    try:
        service = PromptService(db)
        
        # Parse tags string to list
        tag_list = tags.split(",") if tags else None
        
        prompts = await service.list_prompts(
            category=category,
            tags=tag_list,
            search=search
        )
        
        return {
            "success": True,
            "prompts": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "tags": p.tags,
                    "category": p.category,
                    "created_at": p.created_at
                }
                for p in prompts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a prompt template"""
    try:
        service = PromptService(db)
        prompt = await service.update_prompt(
            prompt_id=prompt_id,
            content=data.content,
            description=data.description,
            tags=data.tags,
            category=data.category,
            variables=data.variables
        )
        return {
            "success": True,
            "prompt": {
                "id": prompt.id,
                "name": prompt.name,
                "updated_at": prompt.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a prompt template"""
    try:
        service = PromptService(db)
        await service.delete_prompt(prompt_id)
        return {"success": True, "message": "Prompt deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{prompt_id}/render")
async def render_prompt(
    prompt_id: str,
    variables: dict,
    db: AsyncSession = Depends(get_db_session)
):
    """Render a prompt template with variables"""
    try:
        service = PromptService(db)
        rendered = await service.render_prompt(prompt_id, variables)
        return {
            "success": True,
            "rendered": rendered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
