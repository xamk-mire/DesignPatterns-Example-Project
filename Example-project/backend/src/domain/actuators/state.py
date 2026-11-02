from __future__ import annotations


class IllegalTransitionError(ValueError):
    pass


_TARGETS: dict[str, set[str]] = {
    "idle": {"running", "off", "maintenance", "error"},
    "running": {"idle", "error"},
    "off": {"idle", "error"},
    "maintenance": {"idle", "error"},
    "error": {"idle"},
}


class ActuatorContext:
    def __init__(self, state: str, device_type: str) -> None:
        self.state = state
        self.device_type = device_type

    def transition(self, target: str) -> None:
        if target not in _TARGETS.get(self.state, set()):
            raise IllegalTransitionError(f"Cannot move from {self.state} to {target}")
        self.state = target

    def allowed_targets(self) -> list[str]:
        return sorted(_TARGETS.get(self.state, set()))

    def allowed_commands(self) -> list[str]:
        commands: list[str] = []
        if self.state == "idle" and self.device_type == "water_pump":
            commands.append("start_pump")
        elif self.state == "idle" and self.device_type == "grow_light":
            commands.append("set_light_level")
        elif self.state == "running" and self.device_type == "water_pump":
            commands.append("stop_pump")
        elif self.state == "running" and self.device_type == "grow_light":
            commands.append("set_light_level")
        elif self.state == "off":
            commands.append("power_on")
        elif self.state == "maintenance":
            commands.append("resume")
        elif self.state == "error":
            commands.append("reset")
        if self.state == "idle":
            commands.extend(["power_off", "enter_maintenance"])
        if self.state != "error":
            commands.append("report_fault")
        return commands
