from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar, cast

from email_rules.core.type_defs import Email
from email_rules.rules.type_defs import RuleFilter


T_str = TypeVar("T_str", bound=str)


class GenericRuleTextEq(RuleFilter, Generic[T_str], ABC):
    text: T_str
    case_sensitive: bool = False

    @classmethod
    def create(cls, text: str, case_sensitive: bool = True) -> Self:
        return cls(
            text=cast(T_str, text),
            case_sensitive=case_sensitive,
        )

    def evaluate(self, email: Email) -> bool:
        if not self.case_sensitive:
            return self.text.lower() == self.get_text_from_email(email).lower()
        return self.text == self.get_text_from_email(email)

    @staticmethod
    @abstractmethod
    def get_text_from_email(email: Email) -> T_str:
        pass


class GenericRuleTextContains(RuleFilter, Generic[T_str], ABC):
    text: T_str
    case_sensitive: bool = False

    @classmethod
    def create(cls, text: str, case_sensitive: bool = True) -> Self:
        return cls(
            text=cast(T_str, text),
            case_sensitive=case_sensitive,
        )

    def evaluate(self, email: Email) -> bool:
        if not self.case_sensitive:
            return self.text.lower() in self.get_text_from_email(email).lower()
        return self.text in self.get_text_from_email(email)

    @staticmethod
    @abstractmethod
    def get_text_from_email(email: Email) -> T_str:
        pass


class GenericRuleTextListContains(RuleFilter, Generic[T_str], ABC):
    text: T_str
    case_sensitive: bool = False

    @classmethod
    def create(cls, text: str, case_sensitive: bool = True) -> Self:
        return cls(
            text=cast(T_str, text),
            case_sensitive=case_sensitive,
        )

    def evaluate(self, email: Email) -> bool:
        text_list = self.get_text_list_from_email(email)
        if not self.case_sensitive:
            return self.text.lower() in [text.lower() for text in text_list]
        return self.text in text_list

    @staticmethod
    @abstractmethod
    def get_text_list_from_email(email: Email) -> list[T_str]:
        pass
