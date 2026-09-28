from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.mappers import devices_to_dtos
from application.locations.config_service import LocationConfigService
from application.locations.dto import (
    AssignZoneRequestDto,
    BuildLocationConfigRequestDto,
    LocationConfigDto,
    LocationSummaryDto,
    ZoneDto,
    ZoneRequestDto,
)
from application.locations.zone_assignment_service import AssignmentNotFound, ZoneAssignmentService
from domain.locations.errors import ConfigurationError
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository

router = APIRouter(prefix="/api/locations", tags=["locations"])
assign_router = APIRouter(tags=["devices"])


def get_config_service(db: Session = Depends(get_db)) -> LocationConfigService:
    return LocationConfigService(LocationRepository(db))


def get_assignment_service(db: Session = Depends(get_db)) -> ZoneAssignmentService:
    return ZoneAssignmentService(DeviceRepository(db), LocationRepository(db))


@router.post("/config", response_model=LocationConfigDto, status_code=status.HTTP_201_CREATED)
def create_location_config(
    body: BuildLocationConfigRequestDto,
    service: LocationConfigService = Depends(get_config_service),
) -> LocationConfigDto:
    try:
        return service.build_and_save(body)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[LocationSummaryDto])
def list_locations(service: LocationConfigService = Depends(get_config_service)) -> list[LocationSummaryDto]:
    return service.list_locations()


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
) -> None:
    if not service.delete_location(location_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")


@router.post("/{location_id}/zones", response_model=ZoneDto, status_code=status.HTTP_201_CREATED)
def add_zone(
    location_id: UUID,
    body: ZoneRequestDto,
    service: LocationConfigService = Depends(get_config_service),
) -> ZoneDto:
    try:
        zone = service.add_zone(location_id, body)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return zone


@router.patch("/{location_id}/zones/{zone_id}", response_model=ZoneDto)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    body: ZoneRequestDto,
    service: LocationConfigService = Depends(get_config_service),
) -> ZoneDto:
    try:
        zone = service.update_zone(location_id, zone_id, body)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


@router.delete("/{location_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
) -> None:
    try:
        deleted = service.delete_zone(location_id, zone_id)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")


@router.get("/{location_id}/config", response_model=LocationConfigDto)
def get_location_config(
    location_id: UUID,
    service: LocationConfigService = Depends(get_config_service),
) -> LocationConfigDto:
    config = service.get_config(location_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return config


@router.get("/{location_id}/zones/{zone_id}/devices", response_model=list[DeviceDto])
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    service: ZoneAssignmentService = Depends(get_assignment_service),
) -> list[DeviceDto]:
    try:
        return devices_to_dtos(service.list_devices(location_id, zone_id))
    except AssignmentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@assign_router.patch("/api/devices/{device_id}/zone", status_code=status.HTTP_204_NO_CONTENT)
def assign_device_zone(
    device_id: UUID,
    body: AssignZoneRequestDto,
    service: ZoneAssignmentService = Depends(get_assignment_service),
) -> None:
    try:
        service.assign(device_id, body.zone_id)
    except AssignmentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
