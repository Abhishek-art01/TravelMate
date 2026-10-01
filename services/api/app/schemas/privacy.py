from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ProfileVisibility = Literal["public", "discoverable", "limited", "hidden"]
LocationPrecision = Literal["hidden", "approximate", "destination"]


class PrivacyWrite(BaseModel):
    profile_visibility: ProfileVisibility | None = None
    discovery_visibility: bool | None = None
    location_precision: LocationPrecision | None = None
    allow_exact_location_sharing: bool | None = None
    personalization_enabled: bool | None = None
    communications_enabled: bool | None = None


class PrivacyRead(BaseModel):
    profile_visibility: ProfileVisibility
    discovery_visibility: bool
    location_precision: LocationPrecision
    allow_exact_location_sharing: bool
    personalization_enabled: bool
    communications_enabled: bool
