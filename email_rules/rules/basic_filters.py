from email_rules.core.type_defs import Email, EmailSubject, EmailTo
from email_rules.rules._base_filters import GenericRuleTextEq, GenericRuleTextListContains


class RuleSubjectEq(GenericRuleTextEq[EmailSubject]):
    @staticmethod
    def get_text_from_email(email: Email) -> EmailSubject:
        return email.email_subject


class RuleToEq(GenericRuleTextListContains[EmailTo]):
    @staticmethod
    def get_text_list_from_email(email: Email) -> list[EmailTo]:
        return email.email_to
