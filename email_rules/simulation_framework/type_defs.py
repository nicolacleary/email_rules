from enum import Enum, auto
from typing import Self

from pydantic import BaseModel

from email_rules.core.type_defs import EmailState
from email_rules.rules.type_defs import Rule


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


class RuleFile(BaseModel):
    file_name: str
    rules: list[Rule]


class RuleFileApplicationState(BaseModel):
    current_file_name: str | None
    rule_application_state_history: list[RuleApplicationState]

    @classmethod
    def create_initial_state(cls) -> Self:
        return cls(
            current_file_name=None,
            rule_application_state_history=[RuleApplicationState.create_initial_state()],
        )

    @property
    def last_rule_application_state(self) -> RuleApplicationState:
        return self.rule_application_state_history[-1]
