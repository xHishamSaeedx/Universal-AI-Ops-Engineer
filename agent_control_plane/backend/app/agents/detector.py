"""Detector node - identify anomalies"""
import logging
from typing import Dict, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


async def detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect if system is unhealthy based on symptoms
    
    Returns updated state with is_unhealthy flag
    """
    symptoms = state.get("symptoms", {})
    
    # Extract key metrics
    error_rate = symptoms.get("error_rate", 0)
    pool_health = symptoms.get("pool_health", "healthy")
    avg_response_time = symptoms.get("avg_response_time_ms", 0)
    health_status = symptoms.get("health_status", "healthy")
    
    # Check for chaos indicators in logs
    chaos_indicators = symptoms.get("chaos_indicators", {})
    has_pool_errors = len(chaos_indicators.get("pool_errors", [])) > 0
    has_connection_errors = len(chaos_indicators.get("connection_errors", [])) > 0
    has_timeout_errors = len(chaos_indicators.get("timeout_errors", [])) > 0
    has_target_errors = len(chaos_indicators.get("target_errors", [])) > 0
    
    # Detection criteria
    high_errors = error_rate > settings.anomaly_threshold_error_rate
    critical_pool = pool_health in ["critical", "degraded"]
    slow_response = avg_response_time > 1000  # > 1 second
    unhealthy_status = health_status in ["degraded", "unhealthy", "down"]
    has_errors_in_logs = has_pool_errors or has_connection_errors or has_timeout_errors or has_target_errors
    
    # System is unhealthy if multiple signals indicate issues
    is_unhealthy = (
        (high_errors and critical_pool) or
        (unhealthy_status and has_errors_in_logs) or
        (slow_response and has_errors_in_logs) or
        (has_pool_errors and critical_pool)
    )
    
    if is_unhealthy:
        logger.warning(f"Anomaly detected! Error rate: {error_rate}%, "
                      f"Pool health: {pool_health}, Response time: {avg_response_time}ms")
        logger.warning(f"Log errors - Pool: {len(chaos_indicators.get('pool_errors', []))}, "
                      f"Connection: {len(chaos_indicators.get('connection_errors', []))}, "
                      f"Timeout: {len(chaos_indicators.get('timeout_errors', []))}")
    else:
        logger.info("System appears healthy")
    
    return {
        **state,
        "is_unhealthy": is_unhealthy
    }
