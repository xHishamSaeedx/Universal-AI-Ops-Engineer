"""LLM service for chaos diagnosis"""
import logging
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based diagnosis"""
    
    def __init__(self):
        if not settings.groq_api_key:
            logger.warning("Groq API key not set, LLM diagnosis will be unavailable")
            self.llm = None
        else:
            self.llm = ChatGroq(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                api_key=settings.groq_api_key
            )
    
    async def diagnose_chaos(
        self,
        symptoms: Dict[str, Any],
        logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Diagnose chaos from symptoms and logs
        
        Returns:
            {
                "diagnosis": str,
                "confidence": float,
                "root_cause": str,
                "chaos_type": str
            }
        """
        if not self.llm:
            # Fallback diagnosis without LLM
            return self._fallback_diagnosis(symptoms, logs)
        
        try:
            # Build prompt from symptoms and logs
            prompt = self._build_diagnosis_prompt(symptoms, logs)
            
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            diagnosis_text = response.content
            
            # Parse response
            diagnosis = self._parse_diagnosis(diagnosis_text, symptoms, logs)
            return diagnosis
            
        except Exception as e:
            # Log detailed error information
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Try to extract more details from the exception
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_details = e.response.text
                logger.error(f"LLM diagnosis failed ({error_type}): {error_msg}")
                logger.error(f"API Error Response: {error_details}")
            elif hasattr(e, 'body'):
                logger.error(f"LLM diagnosis failed ({error_type}): {error_msg}")
                logger.error(f"Error Body: {e.body}")
            else:
                logger.error(f"LLM diagnosis failed ({error_type}): {error_msg}")
                logger.debug(f"Full exception: {repr(e)}", exc_info=True)
            
            return self._fallback_diagnosis(symptoms, logs)
    
    def _build_diagnosis_prompt(self, symptoms: Dict[str, Any], logs: Dict[str, Any]) -> str:
        """Build diagnosis prompt from symptoms and logs"""
        prompt = f"""Analyze the following system symptoms and logs to diagnose what chaos or issue is occurring.

SYMPTOMS:
- Health Status: {symptoms.get('health_status', 'unknown')}
- Error Rate: {symptoms.get('error_rate', 0)}%
- Pool Health: {symptoms.get('pool_health', 'unknown')}
- Pool Utilization: {symptoms.get('pool_utilization', 'unknown')}
- Average Response Time: {symptoms.get('avg_response_time_ms', 0)}ms

TARGET SERVER LOGS (recent errors):
{chr(10).join(logs.get('target_errors', [])[:10])}

POSTGRESQL LOGS (recent errors):
{chr(10).join(logs.get('db_errors', [])[:10])}

POOL-RELATED ERRORS:
{chr(10).join(logs.get('pool_errors', [])[:5])}

CONNECTION ERRORS:
{chr(10).join(logs.get('connection_errors', [])[:5])}

Based on these symptoms and logs, diagnose:
1. What type of chaos or issue is occurring? (e.g., "Database connection pool exhaustion", "Database connection failures", "High latency", etc.)
2. What is the root cause?
3. What is your confidence level (0.0 to 1.0)?

Format your response as:
DIAGNOSIS: [brief diagnosis]
ROOT_CAUSE: [root cause analysis]
CONFIDENCE: [0.0-1.0]
CHAOS_TYPE: [type of chaos detected]
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are an expert SRE (Site Reliability Engineer) analyzing system symptoms and logs to diagnose incidents.

You analyze:
- Application health metrics
- Error rates and response times
- Database connection pool status
- Application logs
- PostgreSQL logs

You diagnose issues like:
- Database connection pool exhaustion
- Database connection failures
- High latency
- Service unavailability
- Resource exhaustion

Be specific and actionable in your diagnosis."""
    
    def _parse_diagnosis(
        self,
        response_text: str,
        symptoms: Dict[str, Any],
        logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM response into structured diagnosis"""
        diagnosis = {
            "diagnosis": "Unknown issue",
            "confidence": 0.5,
            "root_cause": "Unable to determine",
            "chaos_type": "unknown"
        }
        
        # Extract fields from response
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith("DIAGNOSIS:"):
                diagnosis["diagnosis"] = line.replace("DIAGNOSIS:", "").strip()
            elif line.startswith("ROOT_CAUSE:"):
                diagnosis["root_cause"] = line.replace("ROOT_CAUSE:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence_str = line.replace("CONFIDENCE:", "").strip()
                    diagnosis["confidence"] = float(confidence_str)
                except ValueError:
                    pass
            elif line.startswith("CHAOS_TYPE:"):
                diagnosis["chaos_type"] = line.replace("CHAOS_TYPE:", "").strip()
        
        # If parsing failed, use fallback
        if diagnosis["diagnosis"] == "Unknown issue":
            return self._fallback_diagnosis(symptoms, logs)
        
        return diagnosis
    
    def _fallback_diagnosis(
        self,
        symptoms: Dict[str, Any],
        logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback diagnosis without LLM"""
        pool_errors = logs.get("pool_errors", [])
        connection_errors = logs.get("connection_errors", [])
        timeout_errors = logs.get("timeout_errors", [])
        
        if pool_errors:
            return {
                "diagnosis": "Database connection pool exhaustion detected",
                "confidence": 0.8,
                "root_cause": "Connection pool has reached its limit, causing timeouts",
                "chaos_type": "pool_exhaustion"
            }
        elif connection_errors:
            return {
                "diagnosis": "Database connection failures",
                "confidence": 0.7,
                "root_cause": "Unable to establish database connections",
                "chaos_type": "connection_failure"
            }
        elif timeout_errors:
            return {
                "diagnosis": "Request timeouts detected",
                "confidence": 0.6,
                "root_cause": "Requests are timing out, possibly due to resource exhaustion",
                "chaos_type": "timeout"
            }
        else:
            return {
                "diagnosis": "System degradation detected",
                "confidence": 0.5,
                "root_cause": "Multiple symptoms indicate system issues",
                "chaos_type": "degradation"
            }
