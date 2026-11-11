# Command — actuator controls

## Problem

The dashboard should offer start, stop, and light-level changes, and it should refuse a command the actuator's state does not allow. Putting that check in the HTTP handler would mix the request with the rules, and a chain of `if command_type` branches would grow with every new command.

## Solution

Each command is an object with `execute(port)` and a `target_state`. A registry maps `start_pump`, `stop_pump`, and `set_light_level` to those classes. The invoker looks up the class and calls `execute`. It does not branch on the type string.

`POST /api/commands` asks the application service to run one command:

1. A missing device, or a device that is not an actuator, is not found.
2. An unknown type returns 400 and writes no `command_log` row.
3. A type missing from `allowed_commands()` for the saved state is stored as `rejected` and returned as 409. The actuator port is not called and the state is unchanged.
4. Otherwise `execute` calls the Phase 9 stack (`build_actuator_port`). `Max run time exceeded` is stored as `failed`, leaves the state unchanged, and leaves the execution-log row the decorator already wrote.
5. After a completed apply, the service saves a new state through `ActuatorContext.transition` when `target_state` differs from the current state. `set_light_level` on a light that is already `running` does not transition. The row is then `success`.

`GET /api/commands?limit=50` lists the newest rows.

## Where to look

| Piece | Path |
|-------|------|
| Commands | `backend/src/domain/commands/` |
| Service | `backend/src/application/commands/service.py` |
| HTTP | `POST /api/commands`, `GET /api/commands` |
| Controls | `frontend/src/components/commands/CommandPanel.tsx` |

## Try this extension

Add a `power_off` command whose `target_state` is `off`, register it, and enable the button only when `allowed_commands` includes it. Leave the state table in `ActuatorContext` unchanged.
