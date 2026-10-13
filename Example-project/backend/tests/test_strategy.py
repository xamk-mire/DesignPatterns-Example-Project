from uuid import uuid4

from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import AggressiveMoistureStrategy, ConservativeMoistureStrategy


def _context(moisture: float | None) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_id=uuid4(),
        zone_name="Bench 1",
        moisture=moisture,
        low=0.2,
        high=0.45,
    )


def test_conservative_waits_when_within_band() -> None:
    recommendation = ConservativeMoistureStrategy().decide(_context(0.30))
    assert recommendation.action == "wait"
    assert "within" in recommendation.reason

    missing = ConservativeMoistureStrategy().decide(_context(None))
    assert missing.action == "wait"
    assert missing.reason == "no moisture sensor in this zone"


def test_aggressive_differs_on_same_context() -> None:
    context = _context(0.30)
    assert ConservativeMoistureStrategy().decide(context).action == "wait"
    aggressive = AggressiveMoistureStrategy().decide(context)
    assert aggressive.action == "irrigate"
