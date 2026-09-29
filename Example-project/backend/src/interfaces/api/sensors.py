from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.readings.service import DeviceNotFound, ReadingDto, ReadingIngest, ReadingRejected
from application.sensors.service import SensorService
from domain.devices.entity import Device
from domain.sensors.entity import Sensor
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class CreateSensorBody(BaseModel):
    type: str
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict = Field(default_factory=dict)
    sampling_interval_seconds: int
    tracking_enabled: bool
    zone_name: str | None = None


def get_sensor_service(db: Session = Depends(get_db)) -> SensorService:
    return SensorService(DeviceRepository(db))


def get_device_repository(db: Session = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)


def get_reading_ingest(db: Session = Depends(get_db)) -> ReadingIngest:
    devices = DeviceRepository(db)
    return ReadingIngest(devices, ReadingRepository(db))


def _from_device(device: Device, zone_name: str | None) -> SensorResponse:
    if device.id is None:
        raise RuntimeError("Persisted sensor is missing an id")
    return SensorResponse(
        id=device.id,
        device_type=device.device_type,
        display_name=device.display_name,
        default_config=device.default_config,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
        zone_name=zone_name,
    )


def _from_created(sensor: Sensor, devices: DeviceRepository) -> SensorResponse:
    if sensor.id is None:
        raise RuntimeError("Persisted sensor is missing an id")
    device = devices.get_device(sensor.id)
    if device is None:
        raise RuntimeError("Persisted sensor is missing a device row")
    return _from_device(device, None)


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorService = Depends(get_sensor_service)) -> list[SensorResponse]:
    return [_from_device(device, zone_name) for device, zone_name in service.list_sensors()]


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    body: CreateSensorBody,
    service: SensorService = Depends(get_sensor_service),
    devices: DeviceRepository = Depends(get_device_repository),
) -> SensorResponse:
    try:
        sensor = service.create_sensor(body.type, body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _from_created(sensor, devices)


@router.post("/{sensor_id}/read", response_model=ReadingDto)
def read_sensor(
    sensor_id: UUID,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> ReadingDto:
    try:
        return ingest.take_reading(sensor_id)
    except DeviceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReadingRejected as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{sensor_id}/readings", response_model=list[ReadingDto])
def list_readings(
    sensor_id: UUID,
    limit: int = Query(default=20, ge=1, le=200),
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> list[ReadingDto]:
    try:
        return ingest.list_readings(sensor_id, limit)
    except DeviceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
