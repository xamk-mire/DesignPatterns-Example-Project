from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import LoggingActuatorDecorator
from infrastructure.adapters.actuators.max_runtime_decorator import MaxRunTimeActuatorDecorator
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository

simulation_adapter = SimulationActuatorAdapter()


def build_actuator_port(session: Session, now: Callable[[], datetime] | None = None) -> ActuatorPort:
    limited = MaxRunTimeActuatorDecorator(
        simulation_adapter,
        ActuatorStateRepository(session),
        now=now,
    )
    return LoggingActuatorDecorator(limited, ExecutionLogRepository(session))
