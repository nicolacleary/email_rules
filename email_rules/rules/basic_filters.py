from email_rules.core import Email, EmailFrom, EmailSubject, EmailTo
from email_rules.rules._base_filters import GenericRuleTextContains, GenericRuleTextEq, GenericRuleTextListContains


class RuleFromEq(GenericRuleTextEq[EmailFrom]):
    @staticmethod
    def get_text_from_email(email: Email) -> EmailFrom:
        return email.email_from


class RuleSubjectContains(GenericRuleTextContains[EmailSubject]):
    @staticmethod
    def get_text_from_email(email: Email) -> EmailSubject:
        return email.email_subject


class RuleSubjectEq(GenericRuleTextEq[EmailSubject]):
    @staticmethod
    def get_text_from_email(email: Email) -> EmailSubject:
        return email.email_subject


class RuleToEq(GenericRuleTextListContains[EmailTo]):
    @staticmethod
    def get_text_list_from_email(email: Email) -> list[EmailTo]:
        return email.email_to
