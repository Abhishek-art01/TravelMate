from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TravelMate API"
    app_environment: str = "development"
    api_version: str = "v1"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "travelmate"
    postgres_user: str = "travelmate"
    postgres_password: str = "travelmate"
    postgres_sslmode: str = "disable"

    mongodb_uri: str = "mongodb://localhost:27017/travelmate"
    redis_url: str = "redis://localhost:6379/0"

    supabase_url: str = "https://example.supabase.co"
    supabase_anon_key: str = "placeholder"
    supabase_service_role_key: str = "placeholder"
    supabase_jwt_secret: str = "placeholder"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
