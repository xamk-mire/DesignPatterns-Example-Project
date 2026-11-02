from uuid import UUID

from pydantic import BaseModel, Field


class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict = Field(default_factory=dict)
    state: str | None = None
    allowed_commands: list[str] = Field(default_factory=list)
    allowed_targets: list[str] = Field(default_factory=list)
