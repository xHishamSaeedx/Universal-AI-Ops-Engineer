import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import health, actions

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
    **Action Server - Remediation Control Plane**
    
    Provides safe, audited endpoints for autonomous incident remediation.
    
    ## Capabilities
    
    - **Container Management**: Restart target API and database containers
    - **Health Verification**: Comprehensive health checks and validation
    - **Chaos Control**: Stop ongoing chaos attacks
    - **Complete Workflows**: End-to-end remediation with verification
    
    ## Safety Features
    
    - Rate limiting on destructive operations
    - Audit logging of all actions
    - Dry-run mode for preview
    - Comprehensive error handling
    
    ## Agent Integration
    
    This server is designed to be called by the Agent Control Plane.
    All endpoints return structured responses for easy parsing.
    
    Example usage:
    ```python
    # Agent calls action server to fix pool exhaustion
    response = await httpx.post(
        "http://action-server:9000/action/remediate-db-pool-exhaustion",
        params={"attack_id": "abc-123"}
    )
    ```
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(actions.router, prefix="/api/v1", tags=["Actions"])

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.app_name} v{settings.version}")
    logger.info(f"🎯 Target API: {settings.target_api_base_url}")
    logger.info(f"📋 Audit Logging: {'Enabled' if settings.enable_audit_logging else 'Disabled'}")
    logger.info(f"🔧 Debug Mode: {'Enabled' if settings.debug else 'Disabled'}")
    logger.info(f"🔒 Scope: Target server remediation only")
    logger.info("=" * 60)
    logger.info("Action server ready to receive remediation requests")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
