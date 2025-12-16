from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/target_server"

    # Application settings
    app_name: str = "Target Server API"
    debug: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()