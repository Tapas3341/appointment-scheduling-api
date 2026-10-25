from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    duration_minutes: int = Field(gt=0)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    name: str
    duration_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    timezone: str = Field(min_length=1, max_length=255)

    @field_validator("display_name", "timezone", mode="before")
    @classmethod
    def trim_string_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("timezone must be a valid IANA timezone.") from exc
        return value


class ProviderProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    display_name: str
    timezone: str
    created_at: datetime
    updated_at: datetime
