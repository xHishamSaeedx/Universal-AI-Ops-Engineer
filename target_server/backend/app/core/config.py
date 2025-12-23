from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/target_server"
    db_pool_size: int = 5
    db_max_overflow: int = 0
    db_pool_timeout: int = 3

    # Application settings
    app_name: str = "Target Server API"
    debug: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # External service settings (for testing env var chaos)
    external_api_key: str = ""

    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()