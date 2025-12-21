"""Agent control routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from ..agents.workflow import create_workflow, AgentState

logger = logging.getLogger(__name__)

router = APIRouter()

# Create workflow instance
workflow = create_workflow()


@router.post("/agent/trigger")
async def trigger_agent() -> Dict[str, Any]:
    """
    Manually trigger incident response workflow
    """
    try:
        logger.info("Manually triggering agent workflow...")
        
        # Initialize state
        initial_state: AgentState = {
            "symptoms": {},
            "diagnosis": "",
            "confidence": 0.0,
            "root_cause": "",
            "chaos_type": "",
            "is_unhealthy": False,
            "is_resolved": False,
            "action_plan": [],
            "execution_results": [],
            "recommendation": ""
        }
        
        # Run workflow
        final_state = await workflow.ainvoke(initial_state)
        
        return {
            "status": "completed",
            "diagnosis": final_state.get("diagnosis", ""),
            "confidence": final_state.get("confidence", 0.0),
            "chaos_type": final_state.get("chaos_type", ""),
            "root_cause": final_state.get("root_cause", ""),
            "recommendation": final_state.get("recommendation", ""),
            "symptoms_summary": final_state.get("symptoms_summary", {})
        }
    except Exception as e:
        logger.error(f"Error running agent workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")


@router.get("/agent/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    Get current agent status
    """
    return {
        "status": "ready",
        "workflow": "monitor -> detect -> gather -> diagnose",
        "monitoring": "active"
    }
