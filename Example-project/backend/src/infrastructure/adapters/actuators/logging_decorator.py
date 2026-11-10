from uuid import UUID

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeExceeded
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository


class LoggingActuatorDecorator(ActuatorPort):
    def __init__(self, inner: ActuatorPort, log: ExecutionLogRepository) -> None:
        self._inner = inner
        self._log = log

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        try:
            self._inner.apply(device_id, command, payload)
        except MaxRunTimeExceeded as exc:
            self._log.insert(
                device_id=device_id,
                success=False,
                policy_applied=["maxRunTime", "logging"],
                message=str(exc),
            )
            raise
        except Exception as exc:
            self._log.insert(
                device_id=device_id,
                success=False,
                policy_applied=["logging"],
                message=str(exc),
            )
            raise
        self._log.insert(
            device_id=device_id,
            success=True,
            policy_applied=["logging"],
            message=None,
        )
