from typing import ClassVar

from email_rules.core.type_defs import Email, EmailState
from email_rules.rules.type_defs import RuleAction, RuleFilter


class RuleAlwaysTrue(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        return True

    def __repr__(self) -> str:
        return "TRUE"


class RuleAlwaysFalse(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        return False

    def __repr__(self) -> str:
        return "FALSE"


class RuleActionDoNothingAndTrackCalls(RuleAction):
    instance: int
    calls: ClassVar[list[int]]

    @staticmethod
    def clear_calls() -> None:
        RuleActionDoNothingAndTrackCalls.calls = []
        assert not RuleActionDoNothingAndTrackCalls.calls, "Could not clear"

    def apply(self, email_state: EmailState) -> EmailState:
        self.calls.append(self.instance)
        return email_state


ALWAYS_TRUE = RuleAlwaysTrue()
ALWAYS_FALSE = RuleAlwaysFalse()
