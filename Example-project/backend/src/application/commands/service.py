from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.actuators.state import ActuatorContext
from domain.commands.invoker import CommandInvoker, command_for
from infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeExceeded
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.command_log_repository import CommandLogRepository, CommandRecord
from infrastructure.persistence.device_repository import DeviceRepository


class DeviceNotFound(Exception):
    pass


class CommandRejected(Exception):
    def __init__(self, record: CommandRecord) -> None:
        self.record = record


class CommandService:
    def __init__(
        self,
        devices: DeviceRepository,
        states: ActuatorStateRepository,
        logs: CommandLogRepository,
        port: ActuatorPort,
        invoker: CommandInvoker | None = None,
    ) -> None:
        self._devices = devices
        self._states = states
        self._logs = logs
        self._port = port
        self._invoker = invoker or CommandInvoker()

    def submit(self, command_type: str, device_id: UUID, payload: dict) -> CommandRecord:
        device = self._devices.get_device(device_id)
        state = self._states.get(device_id)
        if device is None or device.role != "actuator" or state is None:
            raise DeviceNotFound()
        command = command_for(command_type, device_id, payload)
        context = ActuatorContext(state, device.device_type)
        if command.command_type not in context.allowed_commands():
            record = self._logs.insert(
                command_type=command.command_type,
                device_id=device_id,
                payload=payload,
                status="rejected",
                error_message="Command is not allowed in the current state",
            )
            raise CommandRejected(record)
        try:
            self._invoker.run(command, self._port)
        except MaxRunTimeExceeded as exc:
            return self._logs.insert(
                command_type=command.command_type,
                device_id=device_id,
                payload=payload,
                status="failed",
                error_message=str(exc),
            )
        if command.target_state is not None and command.target_state != context.state:
            context.transition(command.target_state)
            self._states.save(device_id, context.state)
        return self._logs.insert(
            command_type=command.command_type,
            device_id=device_id,
            payload=payload,
            status="success",
            error_message=None,
        )

    def list_recent(self, limit: int) -> list[CommandRecord]:
        return self._logs.list_recent(limit)
