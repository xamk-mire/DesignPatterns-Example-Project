# Decorator — actuator policies

## Problem

An actuator command should pass through extra rules, such as a run-time limit and a record of every attempt, without the caller learning how many rules are stacked. A subclass of the simulation adapter would mix those rules into the hardware stand-in. A wrapper keeps each rule separate and leaves `apply` unchanged.

## Solution

Every wrapper implements `ActuatorPort.apply(device_id, command, payload)`. The stack is:

`LoggingActuatorDecorator` → `MaxRunTimeActuatorDecorator` → `SimulationActuatorAdapter`

Logging is outermost. It always inserts one `actuator_execution_log` row, then re-raises. Max-run-time reads `actuator_states`. When the actuator is `running` and `updated_at` is at least 30 minutes before the clock, it raises `Max run time exceeded` and does not call the inner adapter. That row is `success=false` with `policy_applied` `["maxRunTime", "logging"]`. A completed attempt is `success=true` with `policy_applied` `["logging"]` and `message` null. The command string is forwarded and not checked; Phase 10 consults `allowed_commands`.

`GET /api/actuators/executions` lists those rows. `POST /api/actuators/{device_id}/apply` calls the composed port. The route does not decide the policy.

## Where to look

| Piece | Path |
|-------|------|
| Port | `backend/src/domain/actuators/ports.py` |
| Wrappers | `backend/src/infrastructure/adapters/actuators/logging_decorator.py`, `max_runtime_decorator.py` |
| Innermost adapter | `backend/src/infrastructure/adapters/actuators/simulation.py` |
| Composition | `backend/src/application/actuators/compose.py` |
| HTTP | `GET /api/actuators/executions`, `POST /api/actuators/{device_id}/apply` |
| Log | `frontend/src/components/actuators/ExecutionLog.tsx` |

## Try this extension

Add a wrapper that rejects `apply` when the actuator state is `error`, and place it between logging and max-run-time. Leave `SimulationActuatorAdapter` unchanged.
