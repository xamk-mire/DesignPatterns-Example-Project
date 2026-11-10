from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApplyRequestDto(BaseModel):
    command: str
    payload: dict = Field(default_factory=dict)


class ExecutionDto(BaseModel):
    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime
