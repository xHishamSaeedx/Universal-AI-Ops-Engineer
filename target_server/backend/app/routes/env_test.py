from fastapi import APIRouter, HTTPException
from ..core.config import settings

router = APIRouter()


@router.get("/test/env")
async def test_env_usage():
    """
    Test endpoint that uses a specific environment variable (EXTERNAL_API_KEY).
    
    This endpoint is designed to fail when:
    - EXTERNAL_API_KEY is missing from environment
    - EXTERNAL_API_KEY has an invalid/wrong value
    
    This simulates real-world scenarios where services depend on external API keys
    and fail when they're misconfigured.
    """
    # Get the environment variable
    api_key = settings.external_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="EXTERNAL_API_KEY is missing. This service requires a valid API key to function."
        )
    
    # Validate the API key format (basic validation)
    # In real scenarios, this might make an actual API call
    if api_key == "INVALID_VALUE_12345" or len(api_key) < 8:
        raise HTTPException(
            status_code=500,
            detail=f"EXTERNAL_API_KEY has an invalid value. Expected a valid API key, got: {api_key[:10]}..."
        )
    
    # Simulate using the API key (in real app, this would make an API call)
    # For testing purposes, just return success with a masked key
    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
    
    return {
        "status": "success",
        "message": "Successfully validated external API key",
        "key_preview": masked_key,
        "key_length": len(api_key)
    }

