from __future__ import annotations

from enum import StrEnum


class VerificationStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REQUIRES_ACTION = "requires_action"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class VerificationType(StrEnum):
    EMAIL = "email"
    SOCIAL = "social"
    SELFIE = "selfie"
    GOVERNMENT_ID = "government_id"
    VIDEO = "video"


VALID_TRANSITIONS: dict[str, set[str]] = {
    VerificationStatus.NOT_STARTED: {
        VerificationStatus.PENDING,
        VerificationStatus.IN_PROGRESS,
    },
    VerificationStatus.PENDING: {
        VerificationStatus.IN_PROGRESS,
        VerificationStatus.SUBMITTED,
        VerificationStatus.IN_REVIEW,
        VerificationStatus.CANCELLED,
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.IN_PROGRESS: {
        VerificationStatus.SUBMITTED,
        VerificationStatus.IN_REVIEW,
        VerificationStatus.CANCELLED,
        VerificationStatus.EXPIRED,
        VerificationStatus.REQUIRES_ACTION,
    },
    VerificationStatus.SUBMITTED: {
        VerificationStatus.IN_REVIEW,
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.REQUIRES_ACTION,
        VerificationStatus.CANCELLED,
    },
    VerificationStatus.IN_REVIEW: {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.REQUIRES_ACTION,
    },
    VerificationStatus.REQUIRES_ACTION: {
        VerificationStatus.IN_PROGRESS,
        VerificationStatus.SUBMITTED,
        VerificationStatus.EXPIRED,
        VerificationStatus.CANCELLED,
    },
    VerificationStatus.VERIFIED: {
        VerificationStatus.SUSPENDED,
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.REJECTED: {
        VerificationStatus.PENDING,
    },
    VerificationStatus.EXPIRED: {
        VerificationStatus.PENDING,
    },
    VerificationStatus.CANCELLED: {
        VerificationStatus.PENDING,
    },
    VerificationStatus.SUSPENDED: {
        VerificationStatus.IN_REVIEW,
        VerificationStatus.REJECTED,
    },
}


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal verification status transition is attempted."""


def can_transition(current: str, target: str) -> bool:
    if current == target:
        return True
    return target in VALID_TRANSITIONS.get(current, set())


def validate_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        raise InvalidStateTransitionError(
            f"Illegal state transition from '{current}' to '{target}'."
        )
