from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import CommandLogRow


class CommandRecord:
    def __init__(
        self,
        id: UUID,
        command_type: str,
        device_id: UUID,
        payload: dict,
        status: str,
        error_message: str | None,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.command_type = command_type
        self.device_id = device_id
        self.payload = payload
        self.status = status
        self.error_message = error_message
        self.created_at = created_at


class CommandLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(
        self,
        *,
        command_type: str,
        device_id: UUID,
        payload: dict,
        status: str,
        error_message: str | None,
    ) -> CommandRecord:
        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=dict(payload),
            status=status,
            error_message=error_message,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_record(row)

    def list_recent(self, limit: int = 50) -> list[CommandRecord]:
        rows = (
            self._session.query(CommandLogRow)
            .order_by(CommandLogRow.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_record(row) for row in rows]


def _to_record(row: CommandLogRow) -> CommandRecord:
    return CommandRecord(
        id=row.id,
        command_type=row.command_type,
        device_id=row.device_id,
        payload=dict(row.payload or {}),
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
    )
