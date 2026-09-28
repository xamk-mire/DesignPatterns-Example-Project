from uuid import UUID

from sqlalchemy.orm import Session

from domain.devices.entity import Device
from domain.sensors.entity import Sensor
from infrastructure.persistence.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        device = self.save_device(
            Device(
                id=None,
                device_type=sensor.device_type,
                role="sensor",
                device_family="simulation",
                display_name=sensor.display_name,
                default_config=sensor.default_config,
            )
        )
        return Sensor(
            id=device.id,
            device_type=device.device_type,
            display_name=device.display_name,
            default_config=device.default_config,
        )

    def list_sensors(self) -> list[Sensor]:
        devices = self.list_devices(role="sensor")
        return [
            Sensor(
                id=device.id,
                device_type=device.device_type,
                display_name=device.display_name,
                default_config=device.default_config,
            )
            for device in devices
        ]

    def save_device(self, device: Device) -> Device:
        row = DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return self._to_device(row)

    def save_devices(self, devices: list[Device]) -> list[Device]:
        rows = [
            DeviceRow(
                device_type=device.device_type,
                role=device.role,
                device_family=device.device_family,
                display_name=device.display_name,
                default_config=device.default_config,
            )
            for device in devices
        ]
        self._session.add_all(rows)
        self._session.commit()
        for row in rows:
            self._session.refresh(row)
        return [self._to_device(row) for row in rows]

    def get_device(self, device_id: UUID) -> Device | None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            return None
        return self._to_device(row)

    def set_zone(
        self,
        device_id: UUID,
        *,
        zone_id: UUID | None,
        location_id: UUID | None,
    ) -> None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            raise LookupError("Device not found")
        row.zone_id = zone_id
        row.location_id = location_id
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def list_devices(
        self,
        *,
        device_family: str | None = None,
        role: str | None = None,
        zone_id: UUID | None = None,
    ) -> list[Device]:
        query = self._session.query(DeviceRow)
        if device_family is not None:
            query = query.filter(DeviceRow.device_family == device_family)
        if role is not None:
            query = query.filter(DeviceRow.role == role)
        if zone_id is not None:
            query = query.filter(DeviceRow.zone_id == zone_id)
        rows = query.order_by(DeviceRow.created_at.desc()).all()
        return [self._to_device(row) for row in rows]

    @staticmethod
    def _to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or "",
            default_config=dict(row.default_config or {}),
        )
