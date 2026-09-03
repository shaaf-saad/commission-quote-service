from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    vendor_api_url: str = "http://127.0.0.1:8001"
    vendor_api_key: str = "dev-vendor-api-key"
    vendor_timeout_seconds: float = 5.0
    allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173"


settings = Settings()
