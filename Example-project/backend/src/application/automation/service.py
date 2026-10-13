from uuid import UUID

from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import get_strategy
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository

from application.automation.dto import EvaluationDto, StrategySavedDto


class LocationNotFound(Exception):
    pass


class StrategyNotSaved(Exception):
    pass


class AutomationService:
    def __init__(
        self,
        locations: LocationRepository,
        rules: AutomationRepository,
        readings: ReadingRepository,
    ) -> None:
        self._locations = locations
        self._rules = rules
        self._readings = readings

    def set_strategy(self, location_id: UUID, strategy_key: str) -> StrategySavedDto:
        if self._locations.get_config(location_id) is None:
            raise LocationNotFound(str(location_id))
        get_strategy(strategy_key)
        saved = self._rules.upsert(location_id, strategy_key)
        return StrategySavedDto(location_id=location_id, strategy_key=saved)

    def evaluate(self, location_id: UUID) -> EvaluationDto:
        config = self._locations.get_config(location_id)
        if config is None:
            raise LocationNotFound(str(location_id))
        key = self._rules.get_key(location_id)
        if key is None:
            raise StrategyNotSaved("No irrigation strategy is saved for this location")
        strategy = get_strategy(key)
        decisions: list[tuple[str, str, str]] = []
        for zone in config.location.zones:
            if zone.id is None:
                continue
            context = LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.id,
                zone_name=zone.name,
                moisture=self._readings.latest_moisture_for_zone(zone.id),
                low=zone.moisture_threshold_low,
                high=zone.moisture_threshold_high,
            )
            recommendation = strategy.decide(context)
            decisions.append((zone.name, recommendation.action, recommendation.reason))
        irrigating = [item for item in decisions if item[1] == "irrigate"]
        if irrigating:
            zone_name, action, reason = irrigating[0]
            folded_reason = f"{zone_name}: {reason}"
        elif decisions:
            action = "wait"
            folded_reason = "; ".join(f"{zone_name}: {reason}" for zone_name, _, reason in decisions)
        else:
            action = "wait"
            folded_reason = "no zones"
        return EvaluationDto(
            location_id=location_id,
            strategy_key=key,
            action=action,
            reason=folded_reason,
        )
