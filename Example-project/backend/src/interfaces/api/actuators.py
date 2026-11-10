from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.actuators.compose import build_actuator_port
from application.actuators.dto import ApplyRequestDto, ExecutionDto
from infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeExceeded
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


@router.get("/executions", response_model=list[ExecutionDto])
def list_executions(
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ExecutionDto]:
    rows = ExecutionLogRepository(db).list_recent(limit)
    return [
        ExecutionDto(
            id=row.id,
            device_id=row.device_id,
            success=row.success,
            policy_applied=row.policy_applied,
            message=row.message,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/{device_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
def apply_command(
    device_id: UUID,
    body: ApplyRequestDto,
    db: Session = Depends(get_db),
) -> None:
    if DeviceRepository(db).get_device(device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    port = build_actuator_port(db)
    try:
        port.apply(device_id, body.command, body.payload)
    except MaxRunTimeExceeded as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
