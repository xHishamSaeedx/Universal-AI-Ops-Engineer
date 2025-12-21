from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Agent Control Plane Configuration"""
    
    # Application settings
    app_name: str = "Agent Control Plane"
    version: str = "1.0.0"
    debug: bool = True
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 9001
    
    # Target server (monitoring)
    target_api_base_url: str = "http://localhost:8000"
    target_container_name: str = "target_server_api"
    target_db_container_name: str = "target_server_db"
    
    # Action server (remediation) - not connected yet
    action_server_url: str = "http://localhost:9000"
    
    # LLM
    groq_api_key: Optional[str] = None
    llm_model: str = "llama-3.1-70b-versatile"
    llm_temperature: float = 0.3
    
    # RAG (for future use)
    vector_store_path: str = "./data/vector_store"
    runbooks_path: str = "./data/runbooks"
    
    # Monitoring
    poll_interval_seconds: int = 30
    anomaly_threshold_error_rate: float = 50.0
    log_tail_lines: int = 100
    
    # Docker settings for log monitoring
    docker_socket_path: str = "/var/run/docker.sock"  # Linux/Mac
    use_docker_api: bool = True  # Use Docker API instead of docker CLI
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
