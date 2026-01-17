from email_rules.core.type_defs import EmailSubject, EmailTag
from email_rules.exporting._templates import _JinjaTemplate


class ActionTag(_JinjaTemplate):
    tag_name: EmailTag


class FilterSubjectEq(_JinjaTemplate):
    text: EmailSubject
    case_sensitive: bool


class Templates:
    ACTION_TAG = ActionTag
    FILTER_SUBJECT_EQ = FilterSubjectEq
