from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TravelMate API"
    app_environment: str = "development"
    api_version: str = "v1"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://travelmate:travelmate@localhost:5432/travelmate"
    database_pool_size: int = 20
    database_max_overflow: int = 10

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
    supabase_jwt_issuer: str = "https://example.supabase.co/auth/v1"
    supabase_jwt_audience: str = "authenticated"
    supabase_jwks_url: str = "https://example.supabase.co/auth/v1/jwks"
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:4173"
    jwt_cache_ttl_seconds: int = 300

    otel_exporter_otlp_endpoint: str = "http://localhost:4318"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> str:
        if value is None:
            return "http://localhost:3000,http://localhost:5173,http://localhost:4173"
        if isinstance(value, list):
            return ",".join(value)
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
