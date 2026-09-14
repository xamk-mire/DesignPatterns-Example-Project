# Sensors — Factory Method

## Problem

The dashboard needs several kinds of sensors (moisture, light, later temperature). If every HTTP handler constructed `MoistureSensor(...)` or `LightSensor(...)` itself, each new type would edit the router, the service, and the UI entry points.

## Solution

**Factory Method:** an abstract `SensorCreator.create_sensor()` plus concrete creators that own type-specific defaults. Callers ask a registry for a creator by a short key (`moisture` / `light`) and never import the concrete classes.

## Where to look

| Piece | Path |
|-------|------|
| Entity | `backend/src/domain/sensors/entity.py` |
| Creators + `get_creator` | `backend/src/domain/sensors/creators.py` |
| Service (creator then repository) | `backend/src/application/sensors/service.py` |
| Persistence | `backend/src/infrastructure/persistence/` |
| HTTP | `backend/src/interfaces/api/sensors.py` |
| UI | `frontend/src/features/sensors/SensorList.tsx` |

The router must not instantiate sensor types. Unknown keys raise `ValueError` before insert and become HTTP 400.

## Try this extension

Add a `TemperatureSensorCreator` with a distinct `unit` (for example `celsius`) and register it under the key `temperature`. No router change except documenting the new key — `get_creator` should pick it up from the registry.
