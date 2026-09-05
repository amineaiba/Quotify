from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    gemini_api_key: str
    embed_model: str = "gemini-embedding-001"
    agent_model: str = "gemini-3.6-flash"
    jwt_secret: str
    meta_app_secret: str
    meta_verify_token: str
    whatsapp_access_token: str
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
