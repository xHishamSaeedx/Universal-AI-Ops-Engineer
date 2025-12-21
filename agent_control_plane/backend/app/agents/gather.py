"""Gather node - collect all symptoms for diagnosis"""
import logging
from typing import Dict, Any
from ..services.target_client import TargetClient
from ..services.log_monitor import LogMonitor

logger = logging.getLogger(__name__)

target_client = TargetClient()
log_monitor = LogMonitor()


async def gather_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gather comprehensive symptoms for diagnosis
    
    Collects:
    - Current metrics
    - Recent log patterns
    - Historical trends (if available)
    - System state
    """
    logger.info("Gathering comprehensive symptoms...")
    
    symptoms = state.get("symptoms", {})
    
    # Get additional detailed information
    health = await target_client.get_health()
    metrics = await target_client.get_metrics()
    pool_status = await target_client.get_pool_status()
    
    # Get more detailed logs (more lines for better context)
    logs_data = await log_monitor.get_all_logs()
    chaos_indicators = log_monitor.extract_chaos_indicators(logs_data)
    
    # Build comprehensive symptoms
    comprehensive_symptoms = {
        **symptoms,
        "detailed_health": health or {},
        "detailed_metrics": metrics or {},
        "detailed_pool": pool_status.get("pool", {}) if pool_status else {},
        "detailed_logs": logs_data,
        "detailed_chaos_indicators": chaos_indicators,
        "gathered_at": logs_data.get("timestamp")
    }
    
    # Summary for diagnosis
    summary = {
        "health_status": comprehensive_symptoms.get("health_status", "unknown"),
        "error_rate": comprehensive_symptoms.get("error_rate", 0),
        "pool_health": comprehensive_symptoms.get("pool_health", "unknown"),
        "pool_utilization": comprehensive_symptoms.get("pool_utilization", "unknown"),
        "avg_response_time_ms": comprehensive_symptoms.get("avg_response_time_ms", 0),
        "target_errors_count": len(chaos_indicators.get("target_errors", [])),
        "db_errors_count": len(chaos_indicators.get("db_errors", [])),
        "pool_errors_count": len(chaos_indicators.get("pool_errors", [])),
        "connection_errors_count": len(chaos_indicators.get("connection_errors", [])),
        "timeout_errors_count": len(chaos_indicators.get("timeout_errors", []))
    }
    
    logger.info(f"Gathered symptoms: {summary}")
    
    return {
        **state,
        "symptoms": comprehensive_symptoms,
        "symptoms_summary": summary
    }
