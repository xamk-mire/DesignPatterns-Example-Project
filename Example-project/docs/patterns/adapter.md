# Adapter — sensor readings

## Problem

Moisture and light sensors do not share one payload. A simulation kit generates a number in code. A vendor stub speaks in milli-units. An MQTT message arrives as `{ "value", "unit" }`. The rest of the app needs one reading shape and one place that stores it.

## Solution

`SensorPort.read` returns a `Reading` (`device_id`, `value`, `unit`, `source`, `recorded_at`). `SimulationSensorAdapter` and `VendorStubSensorAdapter` implement that port. `MqttSensorAdapter.translate` turns a payload dict into the same `Reading` and does not open a socket.

`ReadingIngest` is the only writer of `sensor_readings`. A one-shot read selects a port and persists. `record` persists a reading that is already translated. `SimulationSampler.run_once(now)` calls ingest for sensors whose `default_config.protocol` is `simulation` and whose `tracking_enabled` is true, and only when the sampling interval has elapsed.

`default_config.vendor_stub: true` selects the vendor stub so it does not collide with `protocol` `simulation` or `mqtt`. A one-shot read of an MQTT device is rejected; that device is ingested through `translate` and `record`.

`ActuatorPort.apply` and `SimulationActuatorAdapter` record the command in memory. Later phases wrap that port. There is no GPIO and no broker in this phase.

## Where to look

| Piece | Path |
|-------|------|
| Port and reading | `backend/src/domain/sensors/ports.py`, `reading.py` |
| Actuator port | `backend/src/domain/actuators/ports.py` |
| Adapters | `backend/src/infrastructure/adapters/sensors/`, `actuators/simulation.py` |
| Selector | `backend/src/infrastructure/adapters/sensors/selector.py` |
| Ingest and sampler | `backend/src/application/readings/` |
| HTTP | `POST /api/sensors/{id}/read`, `GET /api/sensors/{id}/readings`, `PATCH /api/devices/{id}/sampling` |

Sampling columns on `devices` are the source of truth. `default_config.sampling_interval_seconds` is only copied in when a row is created.

## Try this extension

Add a third vendor adapter that reads a different raw key, implement `SensorPort`, and point `vendor_stub` (or a new flag) at it. Leave `ReadingIngest` unchanged.
