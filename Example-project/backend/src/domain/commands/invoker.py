from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command, UnknownCommand
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand

_REGISTRY: dict[str, type[Command]] = {
    StartPumpCommand.command_type: StartPumpCommand,
    StopPumpCommand.command_type: StopPumpCommand,
    SetLightLevelCommand.command_type: SetLightLevelCommand,
}


def command_for(command_type: str, device_id: UUID, payload: dict) -> Command:
    try:
        cls = _REGISTRY[command_type]
    except KeyError:
        raise UnknownCommand(command_type) from None
    return cls(device_id, payload)


class CommandInvoker:
    def run(self, command: Command, port: ActuatorPort) -> None:
        command.execute(port)
