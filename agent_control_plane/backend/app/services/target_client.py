"""HTTP client for target server monitoring"""
import httpx
import logging
from typing import Optional, Dict, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


class TargetClient:
    """Client for monitoring target server"""
    
    def __init__(self):
        self.base_url = settings.target_api_base_url
        self.timeout = 10.0
    
    async def get_health(self) -> Optional[Dict[str, Any]]:
        """Get target server health status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get target health: {e}")
            return None
    
    async def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get target server metrics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/metrics")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get target metrics: {e}")
            return None
    
    async def get_pool_status(self) -> Optional[Dict[str, Any]]:
        """Get connection pool status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/pool/status")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return None
    
    async def is_available(self) -> bool:
        """Check if target server is reachable"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/healthz")
                return response.status_code == 200
        except Exception:
            return False
