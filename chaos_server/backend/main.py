#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.health import router as health_router
from app.routes.break_db_pool import router as break_db_pool_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for the Chaos Server component",
        version=settings.version,
        debug=settings.debug,
    )

    # CORS (configure properly for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
    app.include_router(break_db_pool_router, prefix=settings.api_v1_prefix, tags=["break"])

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "status": "running",
            "docs": {"openapi": "/openapi.json", "swagger": "/docs", "redoc": "/redoc"},
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
