from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import AlertRow


class AlertRecord:
    def __init__(
        self,
        id: UUID,
        location_id: UUID | None,
        zone_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
        status: str,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.location_id = location_id
        self.zone_id = zone_id
        self.device_id = device_id
        self.severity = severity
        self.message = message
        self.event_type = event_type
        self.status = status
        self.created_at = created_at


class AlertRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(
        self,
        *,
        location_id: UUID | None,
        zone_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
        status: str = "active",
    ) -> AlertRecord:
        row = AlertRow(
            location_id=location_id,
            zone_id=zone_id,
            device_id=device_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status=status,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_record(row)

    def list_alerts(
        self,
        *,
        status: str | None = None,
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertRecord]:
        query = self._session.query(AlertRow)
        if status is not None:
            query = query.filter(AlertRow.status == status)
        if location_id is not None:
            query = query.filter(AlertRow.location_id == location_id)
        if zone_id is not None:
            query = query.filter(AlertRow.zone_id == zone_id)
        if since is not None:
            query = query.filter(AlertRow.created_at >= since)
        rows = query.order_by(AlertRow.created_at.desc()).limit(limit).all()
        return [_to_record(row) for row in rows]


def _to_record(row: AlertRow) -> AlertRecord:
    return AlertRecord(
        id=row.id,
        location_id=row.location_id,
        zone_id=row.zone_id,
        device_id=row.device_id,
        severity=row.severity,
        message=row.message,
        event_type=row.event_type,
        status=row.status,
        created_at=row.created_at,
    )
