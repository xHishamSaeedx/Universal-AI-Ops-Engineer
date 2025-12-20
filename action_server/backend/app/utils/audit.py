import logging
import json
from datetime import datetime
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for all action server operations.
    Provides detailed audit trail for compliance and debugging.
    """
    
    def __init__(self):
        self.enabled = settings.enable_audit_logging
        if self.enabled:
            # Configure file handler for audit logs
            audit_handler = logging.FileHandler(settings.audit_log_file)
            audit_handler.setLevel(logging.INFO)
            audit_formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            audit_handler.setFormatter(audit_formatter)
            
            # Create separate audit logger
            self.audit_logger = logging.getLogger("action_server.audit")
            self.audit_logger.setLevel(logging.INFO)
            self.audit_logger.addHandler(audit_handler)
    
    def log(
        self,
        action: str,
        params: dict,
        result: str,
        details: Optional[dict] = None,
        user: str = "agent"
    ) -> None:
        """
        Log an action to the audit trail.
        
        Args:
            action: Name of the action performed
            params: Parameters passed to the action
            result: Result status (success, failed, preview, etc.)
            details: Additional details about the action
            user: User or system that initiated the action
        """
        if not self.enabled:
            return
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "params": params,
            "result": result,
            "user": user,
            "details": details or {}
        }
        
        # Log as JSON for easy parsing
        self.audit_logger.info(json.dumps(audit_entry))
        
        # Also log to main logger for visibility
        logger.info(f"AUDIT: {action} - {result} - User: {user}")
    
    def log_error(
        self,
        action: str,
        error: str,
        params: Optional[dict] = None
    ) -> None:
        """
        Log an error during action execution.
        
        Args:
            action: Name of the action that failed
            error: Error message
            params: Parameters that were used
        """
        self.log(
            action=action,
            params=params or {},
            result="error",
            details={"error": error}
        )
