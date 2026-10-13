from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.automation.dto import EvaluationDto, StrategyRequestDto, StrategySavedDto
from application.automation.service import AutomationService, LocationNotFound, StrategyNotSaved
from domain.automation.strategy import get_strategy
from infrastructure.db import get_db
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository

router = APIRouter(prefix="/api/locations", tags=["automation"])


def get_automation_service(db: Session = Depends(get_db)) -> AutomationService:
    return AutomationService(
        LocationRepository(db),
        AutomationRepository(db),
        ReadingRepository(db),
    )


@router.put("/{location_id}/automation", response_model=StrategySavedDto)
def set_strategy(
    location_id: UUID,
    body: StrategyRequestDto,
    service: AutomationService = Depends(get_automation_service),
) -> StrategySavedDto:
    try:
        get_strategy(body.strategy_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return service.set_strategy(location_id, body.strategy_key)
    except LocationNotFound as exc:
        raise HTTPException(status_code=404, detail="Location not found") from exc


@router.post("/{location_id}/automation/evaluate", response_model=EvaluationDto)
def evaluate(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> EvaluationDto:
    try:
        return service.evaluate(location_id)
    except LocationNotFound as exc:
        raise HTTPException(status_code=404, detail="Location not found") from exc
    except StrategyNotSaved as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
