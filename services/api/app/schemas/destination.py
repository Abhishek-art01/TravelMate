from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DestinationBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=120)
    country: str = Field(min_length=2, max_length=80)
    country_code: str = Field(min_length=2, max_length=3)
    region: str = Field(min_length=1, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    timezone: str = Field(default="UTC", max_length=40)
    category: str = Field(default="general", max_length=40)
    status: str = Field(default="active", pattern="^(active|draft|archived)$")


class DestinationCreate(DestinationBase):
    aliases: list[str] = Field(default_factory=list, max_length=20)


class DestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    country_code: str | None = Field(default=None, min_length=2, max_length=3)
    region: str | None = Field(default=None, min_length=1, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    timezone: str | None = Field(default=None, max_length=40)
    category: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, pattern="^(active|draft|archived)$")
    aliases: list[str] | None = Field(default=None, max_length=20)


class DestinationRead(DestinationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    aliases: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DestinationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    country: str
    country_code: str
    region: str
    city: str | None = None
    category: str
    latitude: float
    longitude: float


class DestinationListResponse(BaseModel):
    items: list[DestinationRead]
    total: int
    limit: int
    offset: int
