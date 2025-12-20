from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Action Server Configuration"""
    
    # Application settings
    app_name: str = "Action Server - Remediation Control"
    version: str = "1.0.0"
    debug: bool = True
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 9000
    
    # Target server configuration (for health checks and verification)
    target_api_base_url: str = "http://localhost:8000"  # Target server backend
    target_docker_compose_path: str = "../../target_server/docker-compose.yml"  # From action_server/backend
    
    # Safety settings
    max_restarts_per_minute: int = 5
    action_timeout_seconds: int = 120
    health_check_timeout_seconds: int = 10
    
    # Audit logging
    enable_audit_logging: bool = True
    audit_log_file: str = "action_server_audit.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
