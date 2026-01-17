from abc import ABC, abstractmethod
from typing import Callable, Self

from pydantic import BaseModel, model_validator

from email_rules.core import Email, EmailState


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


class RuleAction(BaseModel, ABC):
    @abstractmethod
    def apply(self, email_state: EmailState) -> EmailState:
        pass


class Rule(BaseModel):
    filter_expr: RuleFilter
    actions: list[RuleAction]
    comment: str | None = None

    def __repr__(self) -> str:
        actions_repr = "[" + ", ".join([repr(action) for action in self.actions]) + "]"
        comment_repr = f"{self.comment} " if self.comment else ""
        return f"<{comment_repr}filter_expr={repr(self.filter_expr)}, actions={actions_repr}>"
