from fastapi import APIRouter

from app.models.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/healthz")
async def healthz():
    # Simple k8s-style probe endpoint
    return {"status": "ok"}
