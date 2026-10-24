from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegistration(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8)
    role: Literal["customer", "provider"]

    @field_validator("full_name", mode="before")
    @classmethod
    def trim_full_name(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().lower()
        return value


class UserRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    role: Literal["customer", "provider", "admin"]
    created_at: datetime
