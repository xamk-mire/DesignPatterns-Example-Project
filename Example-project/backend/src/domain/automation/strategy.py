from __future__ import annotations

from abc import ABC, abstractmethod

from domain.automation.context import LocationAutomationContext, Recommendation

_NO_SENSOR = "no moisture sensor in this zone"


class AutomationStrategy(ABC):
    key: str

    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        """Choose irrigate or wait from this zone's moisture and thresholds."""


class ConservativeMoistureStrategy(AutomationStrategy):
    key = "conservative"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture is None:
            return Recommendation(action="wait", reason=_NO_SENSOR)
        if context.moisture < context.low:
            return Recommendation(
                action="irrigate",
                reason=f"Moisture {context.moisture:.2f} is below {context.low:.2f}",
            )
        return Recommendation(
            action="wait",
            reason=(
                f"Moisture {context.moisture:.2f} is within {context.low:.2f}–{context.high:.2f}"
            ),
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    key = "aggressive"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture is None:
            return Recommendation(action="wait", reason=_NO_SENSOR)
        midpoint = (context.low + context.high) / 2
        if context.moisture < midpoint:
            return Recommendation(
                action="irrigate",
                reason=f"Moisture {context.moisture:.2f} is below the midpoint {midpoint:.2f}",
            )
        return Recommendation(
            action="wait",
            reason=f"Moisture {context.moisture:.2f} is at or above the midpoint {midpoint:.2f}",
        )


_STRATEGIES: dict[str, AutomationStrategy] = {
    ConservativeMoistureStrategy.key: ConservativeMoistureStrategy(),
    AggressiveMoistureStrategy.key: AggressiveMoistureStrategy(),
}


def get_strategy(key: str) -> AutomationStrategy:
    try:
        return _STRATEGIES[key]
    except KeyError:
        raise ValueError(f"Unknown strategy: {key}") from None
