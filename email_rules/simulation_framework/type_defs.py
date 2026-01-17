from enum import Enum, auto
from typing import Self

from pydantic import BaseModel

from email_rules.core.type_defs import EmailState


class RuleApplicationInterruptState(Enum):
    CONTINUE = auto()
    STOP_PROCESSING_CURRENT_FILE = auto()
    STOP_PROCESSING_ALL_FILES = auto()


class RuleApplicationState(BaseModel):
    email_state: EmailState
    rule_application_interrupt_state: RuleApplicationInterruptState
    current_rule: str | None
    current_rule_applied: bool
    current_action: str | None

    @classmethod
    def create_initial_state(cls) -> Self:
        return cls(
            email_state=EmailState.create_initial_state(),
            rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
            current_rule=None,
            current_rule_applied=False,
            current_action=None,
        )
