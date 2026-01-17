from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Callable, Iterable, Self, Sequence

from pydantic import BaseModel, model_validator

from email_rules.core.type_defs import Email, EmailState


class RuleFilter(BaseModel, ABC):
    @abstractmethod
    def evaluate(self, email: Email) -> bool:
        pass

    def __and__(self, other: "RuleFilter") -> "AggregatedRuleFilter":
        if isinstance(self, AggregatedRuleFilter) and self.is_operator_and():
            self.append_arg(other)
            return self
        return AggregatedRuleFilter.create_and([self, other])

    def __or__(self, other: "RuleFilter") -> "AggregatedRuleFilter":
        if isinstance(self, AggregatedRuleFilter) and not self.is_operator_and():
            self.append_arg(other)
            return self
        return AggregatedRuleFilter.create_or([self, other])

    def __invert__(self) -> "NegatedRuleFilter":
        return NegatedRuleFilter.create_not(self)


class NegatedRuleFilter(RuleFilter):
    arg_1: RuleFilter

    def evaluate(self, email: Email) -> bool:
        return not self.arg_1.evaluate(email=email)

    @staticmethod
    def create_not(arg_1: RuleFilter) -> "NegatedRuleFilter":
        return NegatedRuleFilter(arg_1=arg_1)

    def __repr__(self) -> str:
        return f"~{repr(self.arg_1)}"


class AggregatedRuleFilter(RuleFilter):
    args: list[RuleFilter]
    operator: Callable[[bool, bool], bool]

    @model_validator(mode="after")
    def has_at_least_two_args(self) -> Self:
        if len(self.args) < 2:
            raise ValueError(f"Should have at least 2 args, got: {self.args}")
        return self

    def is_operator_and(self) -> bool:
        return not self.operator(True, False)

    def evaluate(self, email: Email) -> bool:
        result = self.operator(self.args[0].evaluate(email), self.args[1].evaluate(email))
        for arg in self.args[2:]:
            result = self.operator(result, arg.evaluate(email))
        return result

    @staticmethod
    def create_and(args: list[RuleFilter]) -> "AggregatedRuleFilter":
        return AggregatedRuleFilter(
            args=args,
            operator=lambda x, y: x and y,
        )

    @staticmethod
    def create_or(args: list[RuleFilter]) -> "AggregatedRuleFilter":
        return AggregatedRuleFilter(
            args=args,
            operator=lambda x, y: x or y,
        )

    def append_arg(self, arg: RuleFilter) -> None:
        self.args.append(arg)

    def __repr__(self) -> str:
        operator = " & " if self.is_operator_and() else " | "
        return "(" + operator.join([repr(arg) for arg in self.args]) + ")"


class RuleActionApplicationException(Exception):
    pass


class RuleActionStopProcessingCurrentFileException(Exception):
    pass


class RuleActionStopProcessingAllFilesException(Exception):
    pass


class RuleActionApplicationState(Enum):
    CONTINUE = auto()
    STOP_PROCESSING_CURRENT_FILE = auto()
    STOP_PROCESSING_ALL_FILES = auto()


class RuleAction(BaseModel, ABC):
    @abstractmethod
    def apply(self, email_state: EmailState) -> EmailState:
        pass


class RuleApplication(BaseModel):
    email_state: EmailState
    rule_application_state: RuleActionApplicationState
    current_rule: str | None
    current_rule_applied: bool
    current_action: str | None

    @classmethod
    def create_initial_state(cls) -> Self:
        return cls(
            email_state=EmailState.create_initial_state(),
            rule_application_state=RuleActionApplicationState.CONTINUE,
            current_rule=None,
            current_rule_applied=False,
            current_action=None,
        )


class Rule(BaseModel):
    filter_expr: RuleFilter
    actions: list[RuleAction]
    comment: str | None = None

    def apply_rule_to_email(self, email: Email, email_state: EmailState) -> Iterable[RuleApplication]:
        rule_application_state = RuleActionApplicationState.CONTINUE
        if not self.filter_expr.evaluate(email):
            yield RuleApplication(
                email_state=email_state,
                rule_application_state=rule_application_state,
                current_rule=repr(self),
                current_rule_applied=False,
                current_action=None,
            )
            return

        for action in self.actions:
            if rule_application_state != RuleActionApplicationState.CONTINUE:
                break
            try:
                email_state = action.apply(email_state)
            except RuleActionStopProcessingCurrentFileException:
                rule_application_state = RuleActionApplicationState.STOP_PROCESSING_CURRENT_FILE
            except RuleActionStopProcessingAllFilesException:
                rule_application_state = RuleActionApplicationState.STOP_PROCESSING_ALL_FILES

            yield RuleApplication(
                email_state=email_state,
                rule_application_state=rule_application_state,
                current_rule=repr(self),
                current_rule_applied=True,
                current_action=repr(action),
            )

        yield RuleApplication(
            email_state=email_state,
            rule_application_state=rule_application_state,
            current_rule=repr(self),
            current_rule_applied=True,
            current_action=None,
        )

    @staticmethod
    def apply_rules_to_email_iteratively(email: Email, rules: Sequence["Rule"]) -> Iterable[RuleApplication]:
        state = RuleApplication.create_initial_state()
        yield state

        for rule in rules:
            if state.rule_application_state != RuleActionApplicationState.CONTINUE:
                break

            for step in rule.apply_rule_to_email(email, state.email_state):
                yield step
                state = step

    @staticmethod
    def apply_rules_to_email(email: Email, rules: Sequence["Rule"]) -> RuleApplication:
        if len(rules) == 0:
            return RuleApplication.create_initial_state()

        states = list(Rule.apply_rules_to_email_iteratively(email, rules))
        assert len(states) > 0, "We should always have the initial state at least"
        return states[-1]

    def __repr__(self) -> str:
        actions_repr = "[" + ", ".join([repr(action) for action in self.actions]) + "]"
        comment_repr = f"{self.comment} " if self.comment else ""
        return f"<{comment_repr}filter_expr={repr(self.filter_expr)}, actions={actions_repr}>"
