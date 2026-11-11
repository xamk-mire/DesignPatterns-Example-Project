from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommandRequestDto(BaseModel):
    command_type: str
    device_id: UUID
    payload: dict = Field(default_factory=dict)


class CommandLogDto(BaseModel):
    id: UUID
    command_type: str
    device_id: UUID
    payload: dict
    status: str
    error_message: str | None
    created_at: datetime
