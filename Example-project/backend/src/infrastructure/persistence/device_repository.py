from uuid import UUID

from sqlalchemy.orm import Session

from domain.devices.entity import Device
from domain.sensors.entity import Sensor
from infrastructure.persistence.models import DeviceRow, ZoneRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        config = dict(sensor.default_config)
        config.setdefault("protocol", "simulation")
        device = self.save_device(
            Device(
                id=None,
                device_type=sensor.device_type,
                role="sensor",
                device_family="simulation",
                display_name=sensor.display_name,
                default_config=config,
            )
        )
        return Sensor(
            id=device.id,
            device_type=device.device_type,
            display_name=device.display_name,
            default_config=device.default_config,
        )

    def list_sensors(self) -> list[tuple[Device, str | None]]:
        rows = (
            self._session.query(DeviceRow, ZoneRow.name)
            .outerjoin(ZoneRow, DeviceRow.zone_id == ZoneRow.id)
            .filter(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at.desc())
            .all()
        )
        return [(self._to_device(row), zone_name) for row, zone_name in rows]

    def save_device(self, device: Device) -> Device:
        row = DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
            sampling_interval_seconds=_interval_from_config(device.default_config),
            tracking_enabled=device.tracking_enabled,
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
                sampling_interval_seconds=_interval_from_config(device.default_config),
                tracking_enabled=device.tracking_enabled,
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

    def update_sampling(
        self,
        device_id: UUID,
        *,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            return None
        row.sampling_interval_seconds = sampling_interval_seconds
        row.tracking_enabled = tracking_enabled
        self._session.commit()
        self._session.refresh(row)
        return self._to_device(row)

    def list_tracked_simulation_sensors(self) -> list[Device]:
        rows = (
            self._session.query(DeviceRow)
            .filter(DeviceRow.role == "sensor")
            .filter(DeviceRow.tracking_enabled.is_(True))
            .filter(DeviceRow.default_config["protocol"].astext == "simulation")
            .all()
        )
        return [self._to_device(row) for row in rows]

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
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )


def _interval_from_config(config: dict) -> int:
    raw = (config or {}).get("sampling_interval_seconds")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return 300
    return int(raw)
