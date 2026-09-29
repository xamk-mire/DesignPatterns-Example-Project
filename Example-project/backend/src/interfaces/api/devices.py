from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import devices_to_dtos
from application.readings.dto import SamplingDto
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_family_service(db: Session = Depends(get_db)) -> DeviceFamilyService:
    return DeviceFamilyService(DeviceRepository(db))


def get_device_repository(db: Session = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)


class SamplingBody(BaseModel):
    sampling_interval_seconds: int
    tracking_enabled: bool


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = Query(default=None),
    role: str | None = Query(default=None),
    service: DeviceFamilyService = Depends(get_family_service),
) -> list[DeviceDto]:
    return devices_to_dtos(service.list_devices(device_family=family, role=role))


@router.post("/provision", response_model=list[DeviceDto], status_code=status.HTTP_201_CREATED)
def provision_devices(
    family: str = Query(..., description="Device family key: simulation or edge"),
    service: DeviceFamilyService = Depends(get_family_service),
) -> list[DeviceDto]:
    try:
        devices = service.provision_family(family)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return devices_to_dtos(devices)


@router.patch("/{device_id}/sampling", response_model=SamplingDto)
def update_sampling(
    device_id: UUID,
    body: SamplingBody,
    devices: DeviceRepository = Depends(get_device_repository),
) -> SamplingDto:
    if body.sampling_interval_seconds < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sampling_interval_seconds must be at least 5",
        )
    updated = devices.update_sampling(
        device_id,
        sampling_interval_seconds=body.sampling_interval_seconds,
        tracking_enabled=body.tracking_enabled,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return SamplingDto(
        sampling_interval_seconds=updated.sampling_interval_seconds,
        tracking_enabled=updated.tracking_enabled,
    )
