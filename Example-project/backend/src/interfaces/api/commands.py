from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from application.actuators.compose import build_actuator_port
from application.commands.dto import CommandLogDto, CommandRequestDto
from application.commands.service import CommandRejected, CommandService, DeviceNotFound
from domain.commands.base import UnknownCommand
from infrastructure.db import get_db
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.command_log_repository import CommandLogRepository, CommandRecord
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/commands", tags=["commands"])


def _dto(record: CommandRecord) -> CommandLogDto:
    return CommandLogDto(
        id=record.id,
        command_type=record.command_type,
        device_id=record.device_id,
        payload=record.payload,
        status=record.status,
        error_message=record.error_message,
        created_at=record.created_at,
    )


def _service(db: Session) -> CommandService:
    return CommandService(
        DeviceRepository(db),
        ActuatorStateRepository(db),
        CommandLogRepository(db),
        build_actuator_port(db),
    )


@router.post("")
def submit_command(body: CommandRequestDto, db: Session = Depends(get_db)) -> CommandLogDto:
    service = _service(db)
    try:
        record = service.submit(body.command_type, body.device_id, body.payload)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Actuator not found") from None
    except UnknownCommand:
        raise HTTPException(status_code=400, detail="Unknown command") from None
    except CommandRejected as exc:
        return JSONResponse(status_code=409, content=_dto(exc.record).model_dump(mode="json"))
    return _dto(record)


@router.get("", response_model=list[CommandLogDto])
def list_commands(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[CommandLogDto]:
    return [_dto(record) for record in _service(db).list_recent(limit)]
