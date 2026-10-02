from functools import lru_cache
from pathlib import Path

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

    r2_account_id: str = ""
    r2_bucket: str = ""
    r2_endpoint: str = ""
    r2_region: str = "auto"
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    media_max_profile_photos: int = 6
    media_max_profile_photo_size_bytes: int = 10_485_760
    media_signed_url_ttl_seconds: int = 300
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    verification_provider: str = "not_configured"
    verification_provider_region: str = "auto"
    verification_webhook_secret: str = ""
    verification_max_attempts: int = 3
    verification_session_ttl_seconds: int = 1800
    verification_signed_url_ttl_seconds: int = 120
    verification_id_retention_days: int = 30
    verification_selfie_retention_days: int = 30
    verification_video_retention_days: int = 7
    verification_r2_bucket: str = ""

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
    sentry_dsn: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def parse_database_url(cls, value: str | None) -> str:
        if not value:
            return "postgresql+asyncpg://travelmate:travelmate@localhost:5432/travelmate"
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> str:
        if value is None:
            return "http://localhost:3000,http://localhost:5173,http://localhost:4173"
        if isinstance(value, list):
            return ",".join(value)
        return value

    model_config = SettingsConfigDict(
        env_file=tuple(str(parent / ".env") for parent in Path(__file__).resolve().parents) + (".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
