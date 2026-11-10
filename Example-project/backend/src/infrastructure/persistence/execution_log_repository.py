from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import ActuatorExecutionLogRow


class ExecutionRecord:
    def __init__(
        self,
        id: UUID,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.device_id = device_id
        self.success = success
        self.policy_applied = policy_applied
        self.message = message
        self.created_at = created_at


class ExecutionLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(
        self,
        *,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> ExecutionRecord:
        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=list(policy_applied),
            message=message,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_record(row)

    def list_recent(self, limit: int = 20) -> list[ExecutionRecord]:
        rows = (
            self._session.query(ActuatorExecutionLogRow)
            .order_by(ActuatorExecutionLogRow.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_record(row) for row in rows]


def _to_record(row: ActuatorExecutionLogRow) -> ExecutionRecord:
    return ExecutionRecord(
        id=row.id,
        device_id=row.device_id,
        success=row.success,
        policy_applied=list(row.policy_applied or []),
        message=row.message,
        created_at=row.created_at,
    )
