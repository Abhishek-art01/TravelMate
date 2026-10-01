from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.config import Settings, get_settings


class VerificationProviderError(RuntimeError):
    """Base error for verification provider operations."""


class VerificationProviderNotConfiguredError(VerificationProviderError):
    """Raised when an identity verification provider is required but not configured."""


class InvalidWebhookSignatureError(VerificationProviderError):
    """Raised when provider webhook signature is missing, invalid, or expired."""


@dataclass(frozen=True)
class SessionInitParams:
    verification_id: str
    user_id: str
    verification_type: str
    attempt_number: int
    redirect_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SessionResult:
    session_id: str
    session_url: str | None = None
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatusResult:
    session_id: str
    status: str
    decision: str | None = None  # approved, rejected, requires_action
    failure_reason: str | None = None
    provider_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WebhookResult:
    valid: bool
    event_type: str
    provider_session_id: str | None
    verification_id: str | None
    new_status: str | None
    decision: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class VerificationProvider(Protocol):
    provider_name: str

    async def create_verification_session(self, params: SessionInitParams) -> SessionResult: ...

    async def get_verification_status(self, provider_session_id: str) -> ProviderStatusResult: ...

    async def cancel_verification(self, provider_session_id: str) -> None: ...

    async def handle_webhook(self, headers: dict[str, str], raw_body: bytes) -> WebhookResult: ...


class NotConfiguredVerificationProvider:
    provider_name = "not_configured"

    async def create_verification_session(self, params: SessionInitParams) -> SessionResult:
        raise VerificationProviderNotConfiguredError(
            "Identity verification provider is not configured."
        )

    async def get_verification_status(self, provider_session_id: str) -> ProviderStatusResult:
        raise VerificationProviderNotConfiguredError(
            "Identity verification provider is not configured."
        )

    async def cancel_verification(self, provider_session_id: str) -> None:
        raise VerificationProviderNotConfiguredError(
            "Identity verification provider is not configured."
        )

    async def handle_webhook(self, headers: dict[str, str], raw_body: bytes) -> WebhookResult:
        raise VerificationProviderNotConfiguredError(
            "Identity verification provider is not configured."
        )


class MockVerificationProvider:
    """Mock verification provider used strictly for automated tests.

    Provides HMAC signature verification, timestamp replay protection, and
    deterministic status evaluation.
    """
    provider_name = "mock"

    def __init__(self, webhook_secret: str = "mock-secret-key-123"):
        self.webhook_secret = webhook_secret or "mock-secret-key-123"
        self.sessions: dict[str, dict[str, Any]] = {}

    def generate_signature(self, raw_body: bytes, timestamp: str) -> str:
        payload = f"{timestamp}.".encode() + raw_body
        return hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

    async def create_verification_session(self, params: SessionInitParams) -> SessionResult:
        session_id = f"mock_session_{params.verification_id}_{params.attempt_number}"
        session_url = f"https://verify.mock-provider.invalid/session/{session_id}"
        self.sessions[session_id] = {
            "verification_id": params.verification_id,
            "user_id": params.user_id,
            "verification_type": params.verification_type,
            "status": "pending",
            "attempt_number": params.attempt_number,
        }
        return SessionResult(
            session_id=session_id,
            session_url=session_url,
            status="pending",
            metadata={"provider": "mock"},
        )

    async def get_verification_status(self, provider_session_id: str) -> ProviderStatusResult:
        session = self.sessions.get(provider_session_id)
        if not session:
            return ProviderStatusResult(
                session_id=provider_session_id,
                status="not_found",
                failure_reason="Session not found in mock provider",
            )
        return ProviderStatusResult(
            session_id=provider_session_id,
            status=session.get("status", "pending"),
            decision=session.get("decision"),
            failure_reason=session.get("failure_reason"),
            provider_data=session,
        )

    async def cancel_verification(self, provider_session_id: str) -> None:
        if provider_session_id in self.sessions:
            self.sessions[provider_session_id]["status"] = "cancelled"

    async def handle_webhook(self, headers: dict[str, str], raw_body: bytes) -> WebhookResult:
        norm_headers = {k.lower(): v for k, v in headers.items()}
        signature = norm_headers.get("x-signature") or norm_headers.get("x-travelmate-signature")
        timestamp = norm_headers.get("x-timestamp") or norm_headers.get("x-travelmate-timestamp")

        if not signature or not timestamp:
            raise InvalidWebhookSignatureError("Missing required webhook authentication headers.")

        try:
            ts_int = int(timestamp)
        except ValueError as exc:
            raise InvalidWebhookSignatureError("Invalid webhook timestamp format.") from exc

        # 300 second replay window
        current_ts = int(time.time())
        if abs(current_ts - ts_int) > 300:
            raise InvalidWebhookSignatureError("Webhook timestamp is expired or outside the valid replay window.")

        expected_sig = self.generate_signature(raw_body, timestamp)
        if not hmac.compare_digest(signature, expected_sig):
            raise InvalidWebhookSignatureError("Invalid webhook HMAC signature.")

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise VerificationProviderError("Invalid JSON in webhook body.") from exc

        event_type = payload.get("event", "unknown")
        provider_session_id = payload.get("session_id")
        verification_id = payload.get("verification_id")
        new_status = payload.get("status")
        decision = payload.get("decision")
        reason = payload.get("reason")

        if provider_session_id and provider_session_id in self.sessions:
            if new_status:
                self.sessions[provider_session_id]["status"] = new_status
            if decision:
                self.sessions[provider_session_id]["decision"] = decision

        return WebhookResult(
            valid=True,
            event_type=event_type,
            provider_session_id=provider_session_id,
            verification_id=verification_id,
            new_status=new_status,
            decision=decision,
            reason=reason,
            metadata=payload.get("metadata", {}),
        )


def get_verification_provider(settings: Settings | None = None) -> VerificationProvider:
    cfg = settings or get_settings()
    provider_name = (cfg.verification_provider or "").lower().strip()
    if provider_name == "mock":
        return MockVerificationProvider(webhook_secret=cfg.verification_webhook_secret)
    return NotConfiguredVerificationProvider()
