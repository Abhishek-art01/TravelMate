from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class PreferencesWrite(BaseModel):
    dating_intentions: list[str] = Field(default_factory=list, max_length=12)
    dating_preferences: list[str] = Field(default_factory=list, max_length=8)
    discovery_preferences: list[str] = Field(default_factory=list, max_length=8)
    travel_intentions: list[str] = Field(default_factory=list, max_length=12)
    languages: list[str] = Field(default_factory=list, max_length=20)
    interests: list[str] = Field(default_factory=list, max_length=30)
    minimum_age: int = Field(default=18, ge=18, le=100)
    maximum_age: int | None = Field(default=None, ge=18, le=100)

    @model_validator(mode="after")
    def validate_age_range(self) -> PreferencesWrite:
        if self.maximum_age is not None and self.maximum_age < self.minimum_age:
            raise ValueError("maximum_age must be greater than or equal to minimum_age")
        for field_name in (
            "dating_intentions",
            "dating_preferences",
            "discovery_preferences",
            "travel_intentions",
            "languages",
            "interests",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} cannot contain duplicates")
        return self


class PreferencesRead(PreferencesWrite):
    pass
