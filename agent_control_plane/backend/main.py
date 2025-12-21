#!/usr/bin/env python3
"""Agent Control Plane - Main FastAPI application"""
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import health, agent
from app.agents.workflow import create_workflow, AgentState

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Autonomous incident response agent using LangGraph",
    version=settings.version
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
app.include_router(health.router, tags=["health"])
app.include_router(agent.router, prefix="/api/v1", tags=["agent"])


# Background monitoring task
monitoring_task = None
workflow = create_workflow()


async def autonomous_monitoring_loop():
    """Continuously monitor and respond to incidents"""
    logger.info("Starting autonomous monitoring loop...")
    
    while True:
        try:
            # Initialize state
            initial_state: AgentState = {
                "symptoms": {},
                "diagnosis": "",
                "confidence": 0.0,
                "root_cause": "",
                "chaos_type": "",
                "is_unhealthy": False,
                "is_resolved": False,
                "action_plan": [],
                "execution_results": [],
                "recommendation": ""
            }
            
            # Run workflow
            final_state = await workflow.ainvoke(initial_state)
            
            # If unhealthy, log the diagnosis
            if final_state.get("is_unhealthy", False):
                logger.warning(f"Incident detected: {final_state.get('diagnosis', 'Unknown')}")
                logger.warning(f"Chaos type: {final_state.get('chaos_type', 'unknown')}")
                logger.warning(f"Confidence: {final_state.get('confidence', 0.0):.1%}")
            
            # Wait before next monitoring cycle
            await asyncio.sleep(settings.poll_interval_seconds)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            await asyncio.sleep(settings.poll_interval_seconds)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Target server: {settings.target_api_base_url}")
    logger.info(f"Poll interval: {settings.poll_interval_seconds}s")
    
    # Start autonomous monitoring in background
    global monitoring_task
    monitoring_task = asyncio.create_task(autonomous_monitoring_loop())
    logger.info("Autonomous monitoring started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global monitoring_task
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down agent control plane")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.version,
        "status": "healthy"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
