from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.locations.entity import Location, LocationConfig, Zone
from infrastructure.persistence.models import DeviceRow, LocationRow, ZoneRow


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_config(self, config: LocationConfig) -> LocationConfig:
        location = LocationRow(name=config.location.name)
        self._session.add(location)
        try:
            self._session.flush()
            zone_rows = [
                ZoneRow(
                    location_id=location.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=dict(zone.schedule),
                )
                for zone in config.location.zones
            ]
            self._session.add_all(zone_rows)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._session.refresh(location)
        for row in zone_rows:
            self._session.refresh(row)
        return _to_config(location, zone_rows)

    def get_config(self, location_id: UUID) -> LocationConfig | None:
        location = self._session.get(LocationRow, location_id)
        if location is None:
            return None
        zones = (
            self._session.query(ZoneRow)
            .filter(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name)
            .all()
        )
        return _to_config(location, zones)

    def get_zone_location_id(self, zone_id: UUID) -> UUID | None:
        row = self._session.get(ZoneRow, zone_id)
        if row is None:
            return None
        return row.location_id

    def list_locations(self) -> list[tuple[UUID, str]]:
        rows = self._session.query(LocationRow).order_by(LocationRow.created_at.desc()).all()
        return [(row.id, row.name) for row in rows]

    def delete_location(self, location_id: UUID) -> bool:
        location = self._session.get(LocationRow, location_id)
        if location is None:
            return False
        zone_ids = [
            row.id
            for row in self._session.query(ZoneRow.id).filter(ZoneRow.location_id == location_id).all()
        ]
        try:
            self._clear_devices(location_id=location_id, zone_ids=zone_ids)
            self._session.delete(location)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return True

    def add_zone(
        self,
        location_id: UUID,
        *,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict,
    ) -> Zone | None:
        if self._session.get(LocationRow, location_id) is None:
            return None
        row = ZoneRow(
            location_id=location_id,
            name=name,
            moisture_threshold_low=moisture_threshold_low,
            moisture_threshold_high=moisture_threshold_high,
            schedule=dict(schedule),
        )
        try:
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return _to_zone(row)

    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        *,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict,
    ) -> Zone | None:
        row = self._zone_in_location(location_id, zone_id)
        if row is None:
            return None
        row.name = name
        row.moisture_threshold_low = moisture_threshold_low
        row.moisture_threshold_high = moisture_threshold_high
        row.schedule = dict(schedule)
        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return _to_zone(row)

    def zone_names(self, location_id: UUID, *, exclude_zone_id: UUID | None = None) -> list[str] | None:
        if self._session.get(LocationRow, location_id) is None:
            return None
        query = self._session.query(ZoneRow.name).filter(ZoneRow.location_id == location_id)
        if exclude_zone_id is not None:
            query = query.filter(ZoneRow.id != exclude_zone_id)
        return [name for (name,) in query.all()]

    def zone_count(self, location_id: UUID) -> int | None:
        if self._session.get(LocationRow, location_id) is None:
            return None
        return self._session.query(ZoneRow).filter(ZoneRow.location_id == location_id).count()

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> bool:
        row = self._zone_in_location(location_id, zone_id)
        if row is None:
            return False
        try:
            self._clear_devices(location_id=None, zone_ids=[zone_id])
            self._session.delete(row)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return True

    def _zone_in_location(self, location_id: UUID, zone_id: UUID) -> ZoneRow | None:
        row = self._session.get(ZoneRow, zone_id)
        if row is None or row.location_id != location_id:
            return None
        return row

    def _clear_devices(self, *, location_id: UUID | None, zone_ids: list[UUID]) -> None:
        filters = []
        if location_id is not None:
            filters.append(DeviceRow.location_id == location_id)
        if zone_ids:
            filters.append(DeviceRow.zone_id.in_(zone_ids))
        if not filters:
            return
        self._session.query(DeviceRow).filter(or_(*filters)).update(
            {DeviceRow.zone_id: None, DeviceRow.location_id: None},
            synchronize_session=False,
        )


def _to_config(location: LocationRow, zones: list[ZoneRow]) -> LocationConfig:
    return LocationConfig(
        location=Location(
            id=location.id,
            name=location.name,
            zones=tuple(_to_zone(row) for row in zones),
        )
    )


def _to_zone(row: ZoneRow) -> Zone:
    return Zone(
        id=row.id,
        name=row.name,
        moisture_threshold_low=float(row.moisture_threshold_low),
        moisture_threshold_high=float(row.moisture_threshold_high),
        schedule=dict(row.schedule or {}),
    )
