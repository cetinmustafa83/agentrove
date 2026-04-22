from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CustomEnvVar(BaseModel):
    key: str
    value: str


class Persona(BaseModel):
    name: str
    content: str


class UserSettingsBase(BaseModel):
    github_personal_access_token: str | None = None
    custom_instructions: str | None = None
    custom_env_vars: list[CustomEnvVar] | None = None
    personas: list[Persona] | None = None
    notifications_enabled: bool = True

    @field_validator(
        "custom_env_vars",
        "personas",
        mode="before",
    )
    @classmethod
    def _normalize_json_lists(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return []
        raise ValueError(f"Expected list or None, got {type(value).__name__}")


class UserSettingsResponse(UserSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
