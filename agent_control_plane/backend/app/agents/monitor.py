"""Monitor node - continuously observe target server"""
import logging
from typing import Dict, Any
from ..services.target_client import TargetClient
from ..services.log_monitor import LogMonitor
from ..core.config import settings

logger = logging.getLogger(__name__)

target_client = TargetClient()
log_monitor = LogMonitor()


async def monitor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor target server and collect current state
    
    Returns updated state with symptoms
    """
    logger.info("Monitoring target server...")
    
    # Collect health, metrics, and pool status
    health = await target_client.get_health()
    metrics = await target_client.get_metrics()
    pool_status = await target_client.get_pool_status()
    
    # Collect logs
    logs_data = await log_monitor.get_all_logs()
    chaos_indicators = log_monitor.extract_chaos_indicators(logs_data)
    
    # Build symptoms dictionary
    symptoms = {
        "timestamp": logs_data.get("timestamp"),
        "health": health or {},
        "metrics": metrics or {},
        "pool": pool_status.get("pool", {}) if pool_status else {},
        "logs": logs_data,
        "chaos_indicators": chaos_indicators
    }
    
    # Extract key metrics for easy access
    if health:
        symptoms["health_status"] = health.get("status", "unknown")
    
    if metrics:
        symptoms["error_rate"] = metrics.get("error_rate_percent", 0)
        symptoms["avg_response_time_ms"] = metrics.get("avg_response_time_ms", 0)
    
    if pool_status and "pool" in pool_status:
        pool = pool_status["pool"]
        symptoms["pool_health"] = pool.get("pool_health", "unknown")
        symptoms["pool_utilization"] = pool.get("pool_utilization", "unknown")
    
    logger.info(f"Monitoring complete. Health: {symptoms.get('health_status', 'unknown')}, "
                f"Error rate: {symptoms.get('error_rate', 0)}%")
    
    return {
        **state,
        "symptoms": symptoms
    }
