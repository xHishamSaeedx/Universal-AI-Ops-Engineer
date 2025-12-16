#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_tables
from app.routes import health

# Create FastAPI app
app = FastAPI(
    title="Target Server API",
    description="Backend API for the Universal AI Ops Engineer target server",
    version="1.0.0"
)

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