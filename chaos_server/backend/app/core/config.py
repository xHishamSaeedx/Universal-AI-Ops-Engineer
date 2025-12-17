from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Chaos Server API"
    version: str = "0.1.0"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # CORS
    cors_allow_origins: list[str] = ["*"]

    # Target server (victim) base URL
    # Example (docker-compose bridge): http://target_server_api:8000
    target_api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
