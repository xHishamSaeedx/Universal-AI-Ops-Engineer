"""
Rate limit configuration and statistics endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.rate_limit import (
    get_rate_limit_config,
    update_rate_limit_config,
    get_rate_limit_stats,
)

router = APIRouter()


class RateLimitConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    max_requests: Optional[int] = None
    window_seconds: Optional[int] = None


@router.get("/rate_limit/config")
async def get_config():
    """Get current rate limit configuration."""
    return {
        "config": get_rate_limit_config(),
        "status": "ok"
    }


@router.post("/rate_limit/config")
async def update_config(config_update: RateLimitConfigUpdate):
    """
    Update rate limit configuration dynamically.
    
    All fields are optional - only provided fields will be updated.
    """
    if config_update.max_requests is not None and config_update.max_requests < 1:
        raise HTTPException(
            status_code=400,
            detail="max_requests must be at least 1"
        )
    
    if config_update.window_seconds is not None and config_update.window_seconds < 1:
        raise HTTPException(
            status_code=400,
            detail="window_seconds must be at least 1"
        )
    
    update_rate_limit_config(
        enabled=config_update.enabled,
        max_requests=config_update.max_requests,
        window_seconds=config_update.window_seconds,
    )
    
    return {
        "status": "updated",
        "config": get_rate_limit_config(),
    }


@router.get("/rate_limit/stats")
async def get_stats():
    """Get rate limiting statistics including 429 count."""
    stats = get_rate_limit_stats()
    return {
        "stats": stats,
        "status": "ok"
    }

