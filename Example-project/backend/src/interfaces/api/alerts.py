from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from application.alerts.dto import AlertDto
from infrastructure.db import get_db
from infrastructure.persistence.alert_repository import AlertRecord, AlertRepository

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _dto(record: AlertRecord) -> AlertDto:
    return AlertDto(
        id=record.id,
        location_id=record.location_id,
        zone_id=record.zone_id,
        device_id=record.device_id,
        severity=record.severity,
        message=record.message,
        event_type=record.event_type,
        status=record.status,
        created_at=record.created_at,
    )


@router.get("", response_model=list[AlertDto])
def list_alerts(
    status: str = Query(default="active"),
    location_id: UUID | None = None,
    zone_id: UUID | None = None,
    since: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AlertDto]:
    rows = AlertRepository(db).list_alerts(
        status=status,
        location_id=location_id,
        zone_id=zone_id,
        since=since,
        limit=limit,
    )
    return [_dto(row) for row in rows]
