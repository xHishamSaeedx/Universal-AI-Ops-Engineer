from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from env file
    )

    # App
    app_name: str = "Chaos Server API"
    version: str = "0.1.0"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Target server (victim) base URL
    # Example (docker-compose bridge): http://target_server_api:8000
    target_api_base_url: str = "http://localhost:8000"

    # Target server database URL (for direct DB access)
    # Example (docker-compose bridge): postgresql://postgres:password@target_server_db:5432/target_server
    target_database_url: str = "postgresql://postgres:password@localhost:5432/target_server"

    # Target server file paths (for env var chaos)
    # Paths are relative to workspace root or absolute
    target_env_file: str = "target_server/backend/.env"
    target_compose_file: str = "target_server/docker-compose.yml"

    @property
    def cors_allow_origins(self) -> list[str]:
        """Get CORS allowed origins as a list, parsed from environment variable"""
        # Read directly from environment, bypassing pydantic-settings JSON parsing
        cors_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
        if cors_env.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]


settings = Settings()
