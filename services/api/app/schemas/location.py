from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocationUpdate(BaseModel):
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    precision: str = Field(default="approximate", pattern="^(exact|approximate|city|destination|region)$")
    sharing_mode: str = Field(default="approximate", pattern="^(private|approximate|explicit_share)$")
    source: str = Field(default="manual", max_length=32)
    city: str | None = Field(default=None, max_length=80)
    region: str | None = Field(default=None, max_length=80)
    country_code: str | None = Field(default=None, max_length=3)


class UserLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    latitude: float | None = None
    longitude: float | None = None
    approx_latitude: float
    approx_longitude: float
    precision: str
    sharing_mode: str
    source: str
    city: str | None = None
    region: str | None = None
    country_code: str | None = None
    captured_at: datetime
    updated_at: datetime


class PublicLocationRead(BaseModel):
    approx_latitude: float
    approx_longitude: float
    precision: str
    city: str | None = None
    region: str | None = None
    country_code: str | None = None
