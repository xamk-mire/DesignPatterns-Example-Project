from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.sensors.service import SensorService
from domain.sensors.entity import Sensor
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class CreateSensorBody(BaseModel):
    type: str
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict = Field(default_factory=dict)


def get_sensor_service(db: Session = Depends(get_db)) -> SensorService:
    return SensorService(DeviceRepository(db))


def _to_response(sensor: Sensor) -> SensorResponse:
    if sensor.id is None:
        raise RuntimeError("Persisted sensor is missing an id")
    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
    )


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorService = Depends(get_sensor_service)) -> list[SensorResponse]:
    return [_to_response(sensor) for sensor in service.list_sensors()]


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    body: CreateSensorBody,
    service: SensorService = Depends(get_sensor_service),
) -> SensorResponse:
    try:
        sensor = service.create_sensor(body.type, body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(sensor)
