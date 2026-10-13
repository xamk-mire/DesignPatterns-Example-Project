from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.persistence.models import AutomationRuleRow


class AutomationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_key(self, location_id: UUID) -> str | None:
        row = (
            self._session.query(AutomationRuleRow)
            .filter(AutomationRuleRow.location_id == location_id)
            .one_or_none()
        )
        if row is None:
            return None
        return row.strategy_key

    def upsert(self, location_id: UUID, strategy_key: str) -> str:
        row = (
            self._session.query(AutomationRuleRow)
            .filter(AutomationRuleRow.location_id == location_id)
            .one_or_none()
        )
        now = datetime.now(timezone.utc)
        if row is None:
            row = AutomationRuleRow(
                location_id=location_id,
                strategy_key=strategy_key,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.strategy_key = strategy_key
            row.updated_at = now
        self._session.commit()
        self._session.refresh(row)
        return row.strategy_key
