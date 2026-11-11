from domain.events.bus import EventBus
from application.alerts.subscribers import AlertPersistenceSubscriber, MoistureThresholdSubscriber

event_bus = EventBus()
_installed = False


def get_event_bus() -> EventBus:
    global _installed
    if not _installed:
        MoistureThresholdSubscriber(event_bus).subscribe()
        AlertPersistenceSubscriber(event_bus).subscribe()
        _installed = True
    return event_bus
