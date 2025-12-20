import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class TargetServerVerifier:
    """
    Verifies the health and status of the target server.
    Used for post-remediation validation.
    """
    
    async def check_target_health(self) -> dict:
        """
        Comprehensive health check of the target server.
        
        Checks:
        - Overall service status
        - Database connectivity
        - Connection pool health
        - Error rates
        - Response times
        
        Returns:
            Dict with comprehensive health assessment
        """
        target_base_url = settings.target_api_base_url.rstrip("/")
        timeout = httpx.Timeout(settings.health_check_timeout_seconds)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # Check health endpoint
                health_resp = await client.get(f"{target_base_url}/api/v1/health")
                health_data = health_resp.json() if health_resp.status_code == 200 else {}
                
                # Check metrics endpoint
                try:
                    metrics_resp = await client.get(f"{target_base_url}/api/v1/metrics")
                    metrics_data = metrics_resp.json() if metrics_resp.status_code == 200 else {}
                except Exception as e:
                    logger.warning(f"Failed to fetch metrics: {str(e)}")
                    metrics_data = {}
                
                # Check pool status endpoint
                try:
                    pool_resp = await client.get(f"{target_base_url}/api/v1/pool/status")
                    pool_data = pool_resp.json() if pool_resp.status_code == 200 else {}
                except Exception as e:
                    logger.warning(f"Failed to fetch pool status: {str(e)}")
                    pool_data = {}
                
                # Extract key metrics
                pool_health = pool_data.get("pool", {}).get("pool_health", "unknown")
                pool_utilization = pool_data.get("pool", {}).get("pool_utilization", "unknown")
                error_rate = metrics_data.get("application", {}).get("error_rate_percent", 100)
                avg_response_time = metrics_data.get("application", {}).get("avg_response_time_ms", 0)
                
                # Determine overall health
                is_healthy = (
                    health_data.get("status") == "ok" and
                    pool_health in ["healthy", "degraded"] and
                    error_rate < 20  # Allow some errors during recovery
                )
                
                return {
                    "is_healthy": is_healthy,
                    "health_status": health_data.get("status", "unknown"),
                    "database_status": health_data.get("services", {}).get("database", {}).get("status", "unknown"),
                    "pool_health": pool_health,
                    "pool_utilization": pool_utilization,
                    "error_rate_percent": error_rate,
                    "avg_response_time_ms": avg_response_time,
                    "details": {
                        "health_check_passed": health_resp.status_code == 200,
                        "metrics_available": bool(metrics_data),
                        "pool_status_available": bool(pool_data)
                    }
                }
                
            except httpx.ConnectError as e:
                logger.error(f"Cannot connect to target server: {str(e)}")
                return {
                    "is_healthy": False,
                    "error": "connection_failed",
                    "message": f"Cannot connect to target server at {target_base_url}",
                    "details": str(e)
                }
                
            except httpx.TimeoutException as e:
                logger.error(f"Health check timed out: {str(e)}")
                return {
                    "is_healthy": False,
                    "error": "timeout",
                    "message": "Health check timed out",
                    "details": str(e)
                }
                
            except Exception as e:
                logger.error(f"Health verification failed: {str(e)}")
                return {
                    "is_healthy": False,
                    "error": "unknown",
                    "message": "Unexpected error during health verification",
                    "details": str(e)
                }
    
    async def test_target_connectivity(self) -> bool:
        """
        Quick connectivity test to the target server.
        
        Returns:
            True if target is reachable, False otherwise
        """
        target_base_url = settings.target_api_base_url.rstrip("/")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{target_base_url}/api/v1/health")
                return resp.status_code == 200
        except Exception:
            return False
