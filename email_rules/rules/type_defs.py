from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Callable, Self

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


class Rule(BaseModel):
    filter_expr: RuleFilter
    actions: list[RuleAction]
    comment: str | None = None

    def apply_rule_to_email(
        self, email: Email, email_state: EmailState
    ) -> tuple[EmailState, RuleActionApplicationState]:
        rule_application_state = RuleActionApplicationState.CONTINUE
        if not self.filter_expr.evaluate(email):
            return email_state, rule_application_state

        for action in self.actions:
            if rule_application_state != RuleActionApplicationState.CONTINUE:
                break
            try:
                email_state = action.apply(email_state)
            except RuleActionStopProcessingCurrentFileException:
                rule_application_state = RuleActionApplicationState.STOP_PROCESSING_CURRENT_FILE
            except RuleActionStopProcessingAllFilesException:
                rule_application_state = RuleActionApplicationState.STOP_PROCESSING_ALL_FILES

        return email_state, rule_application_state

    @staticmethod
    def apply_rules_to_email(email: Email, rules: list["Rule"]) -> tuple[EmailState, RuleActionApplicationState]:
        email_state = EmailState.create_initial_state()
        rule_application_state = RuleActionApplicationState.CONTINUE

        for rule in rules:
            if rule_application_state != RuleActionApplicationState.CONTINUE:
                break
            email_state, rule_application_state = rule.apply_rule_to_email(email, email_state)

        return email_state, rule_application_state
