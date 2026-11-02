from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import ActuatorStateRow


class ActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, device_id: UUID) -> str | None:
        row = self._session.get(ActuatorStateRow, device_id)
        if row is None:
            return None
        return row.state

    def list_for(self, device_ids: list[UUID]) -> dict[UUID, str]:
        if not device_ids:
            return {}
        rows = (
            self._session.query(ActuatorStateRow)
            .filter(ActuatorStateRow.device_id.in_(device_ids))
            .all()
        )
        return {row.device_id: row.state for row in rows}

    def ensure_idle(self, device_ids: list[UUID]) -> None:
        if not device_ids:
            return
        existing = set(self.list_for(device_ids))
        now = datetime.now(timezone.utc)
        for device_id in device_ids:
            if device_id in existing:
                continue
            self._session.add(
                ActuatorStateRow(device_id=device_id, state="idle", updated_at=now)
            )
        self._session.commit()

    def save(self, device_id: UUID, state: str) -> None:
        row = self._session.get(ActuatorStateRow, device_id)
        now = datetime.now(timezone.utc)
        if row is None:
            row = ActuatorStateRow(device_id=device_id, state=state, updated_at=now)
            self._session.add(row)
        else:
            row.state = state
            row.updated_at = now
        self._session.commit()
