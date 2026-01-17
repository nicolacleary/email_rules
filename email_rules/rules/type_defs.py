from abc import ABC, abstractmethod
from typing import Callable

from pydantic import BaseModel

from email_rules.core.type_defs import Email, EmailState


class RuleFilter(BaseModel, ABC):
    @abstractmethod
    def evaluate(self, email: Email) -> bool:
        pass

    def __and__(self, other: "RuleFilter") -> "AggregatedRuleFilter":
        return AggregatedRuleFilter.create_and(self, other)

    def __or__(self, other: "RuleFilter") -> "AggregatedRuleFilter":
        return AggregatedRuleFilter.create_or(self, other)

    def __invert__(self) -> "NegatedRuleFilter":
        return NegatedRuleFilter.create_not(self)


class NegatedRuleFilter(RuleFilter):
    arg_1: RuleFilter

    def evaluate(self, email: Email) -> bool:
        return not self.arg_1.evaluate(email=email)

    @staticmethod
    def create_not(arg_1: RuleFilter) -> "NegatedRuleFilter":
        return NegatedRuleFilter(arg_1=arg_1)


class AggregatedRuleFilter(RuleFilter):
    arg_1: RuleFilter
    arg_2: RuleFilter
    operator: Callable[[bool, bool], bool]

    def is_operator_and(self) -> bool:
        return not self.operator(True, False)

    def evaluate(self, email: Email) -> bool:
        return self.operator(self.arg_1.evaluate(email), self.arg_2.evaluate(email))

    @staticmethod
    def create_and(arg_1: RuleFilter, arg_2: RuleFilter) -> "AggregatedRuleFilter":
        return AggregatedRuleFilter(
            arg_1=arg_1,
            arg_2=arg_2,
            operator=lambda x, y: x and y,
        )

    @staticmethod
    def create_or(arg_1: RuleFilter, arg_2: RuleFilter) -> "AggregatedRuleFilter":
        return AggregatedRuleFilter(
            arg_1=arg_1,
            arg_2=arg_2,
            operator=lambda x, y: x or y,
        )


class RuleAction(BaseModel, ABC):
    @abstractmethod
    def apply(self, email_state: EmailState) -> EmailState:
        pass


class Rule(BaseModel):
    filter_expr: RuleFilter
    actions: list[RuleAction]

    def apply_rule_to_email(self, email: Email, email_state: EmailState) -> EmailState:
        if not self.filter_expr.evaluate(email):
            return email_state

        for action in self.actions:
            email_state = action.apply(email_state)

        return email_state
