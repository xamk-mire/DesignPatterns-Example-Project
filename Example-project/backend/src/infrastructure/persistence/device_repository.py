from sqlalchemy.orm import Session

from domain.sensors.entity import Sensor
from infrastructure.persistence.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return self._to_sensor(row)

    def list_sensors(self) -> list[Sensor]:
        rows = (
            self._session.query(DeviceRow)
            .filter(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at.desc())
            .all()
        )
        return [self._to_sensor(row) for row in rows]

    @staticmethod
    def _to_sensor(row: DeviceRow) -> Sensor:
        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name or "",
            default_config=dict(row.default_config or {}),
        )
