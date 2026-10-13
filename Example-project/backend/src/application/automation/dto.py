from uuid import UUID

from pydantic import BaseModel


class StrategyRequestDto(BaseModel):
    strategy_key: str


class StrategySavedDto(BaseModel):
    location_id: UUID
    strategy_key: str


class EvaluationDto(BaseModel):
    location_id: UUID
    strategy_key: str
    action: str
    reason: str
