"""LangGraph workflow for autonomous incident response"""
from typing import TypedDict
from langgraph.graph import StateGraph, END
import logging
from .monitor import monitor_node
from .detector import detector_node
from .gather import gather_node
from .diagnoser import diagnoser_node

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent workflow"""
    # Inputs
    symptoms: dict  # Logs, metrics, health status
    
    # Analysis
    diagnosis: str  # "DB connection pool exhaustion"
    confidence: float  # 0.0 to 1.0
    root_cause: str  # Investigation results
    chaos_type: str  # Type of chaos detected
    
    # Detection flags
    is_unhealthy: bool  # Whether system is unhealthy
    is_resolved: bool  # Whether issue is resolved
    
    # Action (not connected yet)
    action_plan: list  # Steps to take
    execution_results: list  # Action outcomes
    
    # Outcome
    recommendation: str


def create_workflow():
    """Create the LangGraph workflow for incident response"""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("monitor", monitor_node)
    workflow.add_node("detect", detector_node)
    workflow.add_node("gather", gather_node)
    workflow.add_node("diagnose", diagnoser_node)
    
    # Define flow
    workflow.set_entry_point("monitor")
    workflow.add_edge("monitor", "detect")
    
    # Conditional edge: if unhealthy, gather symptoms; otherwise, end (system is healthy)
    def route_after_detect(state: AgentState) -> str:
        """Route after detection based on health status"""
        if state.get("is_unhealthy", False):
            return "gather"
        return "end"  # System is healthy, end this workflow cycle
    
    workflow.add_conditional_edges(
        "detect",
        route_after_detect,
        {
            "gather": "gather",
            "end": END
        }
    )
    
    workflow.add_edge("gather", "diagnose")
    workflow.add_edge("diagnose", END)
    
    return workflow.compile()
