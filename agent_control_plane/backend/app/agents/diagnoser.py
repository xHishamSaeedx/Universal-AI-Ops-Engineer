"""Diagnoser node - use LLM to diagnose chaos from symptoms"""
import logging
from typing import Dict, Any
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

llm_service = LLMService()


async def diagnoser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagnose chaos using LLM based on symptoms and logs
    
    Returns updated state with diagnosis, confidence, root_cause, and chaos_type
    """
    logger.info("Diagnosing chaos from symptoms...")
    
    symptoms = state.get("symptoms", {})
    symptoms_summary = state.get("symptoms_summary", {})
    
    # Prepare logs for diagnosis
    chaos_indicators = symptoms.get("chaos_indicators", {}) or symptoms.get("detailed_chaos_indicators", {})
    
    logs_for_diagnosis = {
        "target_errors": chaos_indicators.get("target_errors", [])[:20],  # Limit for LLM context
        "db_errors": chaos_indicators.get("db_errors", [])[:20],
        "pool_errors": chaos_indicators.get("pool_errors", [])[:10],
        "connection_errors": chaos_indicators.get("connection_errors", [])[:10],
        "timeout_errors": chaos_indicators.get("timeout_errors", [])[:10]
    }
    
    # Call LLM service for diagnosis
    diagnosis_result = await llm_service.diagnose_chaos(
        symptoms=symptoms_summary,
        logs=logs_for_diagnosis
    )
    
    logger.info(f"Diagnosis: {diagnosis_result.get('diagnosis', 'Unknown')}")
    logger.info(f"Confidence: {diagnosis_result.get('confidence', 0.0)}")
    logger.info(f"Chaos Type: {diagnosis_result.get('chaos_type', 'unknown')}")
    logger.info(f"Root Cause: {diagnosis_result.get('root_cause', 'Unknown')}")
    
    # Build recommendation
    recommendation = f"""
Based on the analysis:
- Issue: {diagnosis_result.get('diagnosis', 'Unknown issue')}
- Root Cause: {diagnosis_result.get('root_cause', 'Unable to determine')}
- Confidence: {diagnosis_result.get('confidence', 0.0):.1%}
- Chaos Type: {diagnosis_result.get('chaos_type', 'unknown')}

Recommended actions (not yet connected to action server):
1. Review the diagnosis above
2. Check system metrics and logs
3. Consider manual intervention if needed
"""
    
    return {
        **state,
        "diagnosis": diagnosis_result.get("diagnosis", "Unknown issue"),
        "confidence": diagnosis_result.get("confidence", 0.0),
        "root_cause": diagnosis_result.get("root_cause", "Unable to determine"),
        "chaos_type": diagnosis_result.get("chaos_type", "unknown"),
        "recommendation": recommendation
    }
