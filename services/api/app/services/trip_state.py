from __future__ import annotations

from enum import Enum


class TripStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TripVisibility(str, Enum):
    PRIVATE = "private"
    MATCHES_ONLY = "matches_only"
    DISCOVERABLE = "discoverable"
    PUBLIC = "public"


class CompanionPreference(str, Enum):
    TRAVELLING_ALONE = "travelling_alone"
    OPEN_TO_COMPANION = "open_to_companion"
    TRAVELLING_WITH_GROUP = "travelling_with_group"


VALID_TRIP_TRANSITIONS: dict[str, set[str]] = {
    TripStatus.DRAFT.value: {TripStatus.PLANNED.value, TripStatus.CANCELLED.value},
    TripStatus.PLANNED.value: {
        TripStatus.ACTIVE.value,
        TripStatus.CANCELLED.value,
        TripStatus.ARCHIVED.value,
        TripStatus.DRAFT.value,
    },
    TripStatus.ACTIVE.value: {
        TripStatus.COMPLETED.value,
        TripStatus.CANCELLED.value,
    },
    TripStatus.COMPLETED.value: {TripStatus.ARCHIVED.value},
    TripStatus.CANCELLED.value: {TripStatus.ARCHIVED.value, TripStatus.DRAFT.value},
    TripStatus.ARCHIVED.value: set(),
}


def can_transition_trip(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return True
    allowed = VALID_TRIP_TRANSITIONS.get(current_status, set())
    return new_status in allowed
