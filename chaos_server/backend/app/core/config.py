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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
