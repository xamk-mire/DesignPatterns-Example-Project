# State — actuator lifecycle

## Problem

A pump or grow light is not only a device row. It is idle, running, off, in maintenance, or in error. The dashboard and later command handling need the current state and the actions that state allows. An illegal change must leave the stored state as it was.

## Solution

`ActuatorContext` holds `state` and `device_type`. `transition(target)` raises `IllegalTransitionError` before any save when the edge is missing. `POST /api/devices/{id}/transition` loads the row, calls `transition`, and writes only after that succeeds. A missing device or a non-actuator returns 404. An illegal target returns 409.

Each actuator has one `actuator_states` row, keyed by `device_id`. Provisioning a kit inserts `idle` for its actuators. The migration also inserts `idle` for actuators that already existed. Sensors have no state row; their device JSON uses `null` and empty command lists.

## Legal targets

| From | To |
|------|----|
| `idle` | `running`, `off`, `maintenance`, `error` |
| `running` | `idle`, `error` |
| `off` | `idle`, `error` |
| `maintenance` | `idle`, `error` |
| `error` | `idle` |

`running` → `maintenance` is illegal.

## Commands

| State | Commands |
|-------|----------|
| `idle` + `water_pump` | `start_pump`, `power_off`, `enter_maintenance`, `report_fault` |
| `idle` + `grow_light` | `set_light_level`, `power_off`, `enter_maintenance`, `report_fault` |
| `running` + `water_pump` | `stop_pump`, `report_fault` |
| `running` + `grow_light` | `set_light_level`, `report_fault` |
| `off` | `power_on`, `report_fault` |
| `maintenance` | `resume`, `report_fault` |
| `error` | `reset` |

The device list also returns `allowed_targets` so the card can offer only legal next states. The router does not branch on the current state.

## Where to look

| Piece | Path |
|-------|------|
| Context and edges | `backend/src/domain/actuators/state.py` |
| Save | `backend/src/infrastructure/persistence/actuator_state_repository.py` |
| HTTP | `POST /api/devices/{id}/transition` |
| Badges | `frontend/src/components/devices/DeviceList.tsx` |

## Try this extension

Add `running` → `maintenance` as a legal edge inside `ActuatorContext` and give that state a `service` command. Leave the route handler unchanged.
