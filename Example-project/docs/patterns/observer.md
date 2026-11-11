# Observer — alerts from domain events

## Problem

A low moisture reading, a failed command, and an actuator fault should each leave a record the dashboard can show after a refresh. Writing that record inside the reading adapter, the command router, or the state router would tie those actions to the alerts table. A later WebSocket feed would then need a second copy of the same rules.

## Solution

`EventBus` keeps a list of handlers for each event class. `publish` calls the handlers for that class. Publishers do not import `AlertRepository`.

`ReadingIngest.take_reading` and `ReadingIngest.record` insert the reading, then publish `ReadingCreated` when `tracking_enabled` is true. The event carries `device_id`, `value`, `unit`, `source`, `recorded_at`, and the device's `location_id` and `zone_id`. Manual read, the sampler, and a translated MQTT payload all use this path. Tracking off still stores the row and publishes nothing.

`MoistureThresholdSubscriber` listens for `ReadingCreated`. A moisture value strictly below the zone's low threshold publishes `ThresholdCrossed`. A reading with no zone does not.

`CommandService` publishes `CommandFailed` after a decorator failure. `ActuatorTransitionService` publishes `ActuatorEnteredError` after a successful transition to `error`.

`AlertPersistenceSubscriber` inserts an active `alerts` row:

- `threshold.crossed`, severity `warning`, message `Moisture below zone low`
- `command.failed`, severity `warning`, message from the failure
- `state.changed`, severity `critical`, message `Actuator entered error`

`location_id` and `zone_id` are copied from the event. Both stay null when the device is unassigned.

`GET /api/alerts` lists active rows, newest first. Optional filters are `location_id`, `zone_id`, and `since`. The Events panel polls that route every 5 seconds. `frontend/src/services/realtime.ts` is a no-op until Phase 12 adds a WebSocket on this same bus.

## Where to look

| Piece | Path |
|-------|------|
| Events and bus | `backend/src/domain/events/` |
| Subscribers | `backend/src/application/alerts/subscribers.py` |
| Shared bus | `backend/src/application/alerts/wiring.py` |
| HTTP | `GET /api/alerts` |
| Feed | `frontend/src/components/alerts/EventFeed.tsx` |
| Realtime stub | `frontend/src/services/realtime.ts` |

## Try this extension

Add a subscriber that publishes `ThresholdCrossed` when moisture rises back above the zone high threshold, and persist it as `severity="info"`. Leave `ReadingIngest` publishing only `ReadingCreated`.
