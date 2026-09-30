from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthProviderConfig:
    provider: str = "supabase"
    url: str = "https://example.supabase.co"
    anon_key: str = "placeholder"
    service_key: str = "placeholder"
    jwt_secret: str = "placeholder"


class SupabaseAuthGateway:
    """Abstract gateway used to isolate Supabase-specific auth logic from app services."""

    def __init__(self, config: AuthProviderConfig):
        self.config = config

    def get_provider_name(self) -> str:
        return self.config.provider

    def is_configured(self) -> bool:
        return bool(self.config.url and self.config.anon_key and self.config.service_key)
