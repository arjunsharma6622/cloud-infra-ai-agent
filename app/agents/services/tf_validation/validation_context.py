from dataclasses import dataclass, field
from pathlib import Path
from .logger import ValidationLogger
from .workspace import create_workspace
from app.agents.state import AgentState
from datetime import datetime
import uuid

@dataclass
class ValidationContext:
    validation_run_id: str
    attempt: int

    _workspace: Path | None = field(default=None, init=False, repr=False)
    _logger: ValidationLogger | None = field(default=None, init=False, repr=False)

    @property
    def workspace(self) -> Path:
        # lazily create workspace only when first accessed
        if self._workspace is None:
            self._workspace = create_workspace(
                self.validation_run_id,
                self.attempt
            )

        return self._workspace

    @property
    def logger(self) -> ValidationLogger:
        # lazily create logger
        if self._logger is None:
            self._logger = ValidationLogger(
                self.workspace
            )

        return self._logger

    @classmethod
    def from_state(cls, state: AgentState):
        # build validation context from langraph state

        validation_run_id = state.get("validation_run_id")

        if not validation_run_id:
            validation_run_id = (
                f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
            )

        attempt = state["validation_attempts"]+1

        return cls(
            validation_run_id=validation_run_id,
            attempt=attempt
        )
    