#!/usr/bin/env python3

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_tables
from app.routes import health, pool, env_test
import time

# Create FastAPI app
app = FastAPI(
    title="Target Server API",
    description="Backend API for the Universal AI Ops Engineer target server",
    version="1.0.0"
)

# Middleware to track request metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics for observability"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Track successful requests
        if response.status_code < 400:
            health._success_count += 1
        else:
            health._error_count += 1
        
        # Track response time
        duration_ms = (time.time() - start_time) * 1000
        health._request_times.append(duration_ms)
        
        return response
    except Exception:
        # Track errors
        health._error_count += 1
        duration_ms = (time.time() - start_time) * 1000
        health._request_times.append(duration_ms)
        raise

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(pool.router, prefix="/api/v1", tags=["pool"])
app.include_router(env_test.router, prefix="/api/v1", tags=["test"])

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Target Server API is running", "status": "healthy"}

@app.get("/healthz")
async def healthz():
    """Simple health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )