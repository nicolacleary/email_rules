from email_rules.core.type_defs import EmailSubject, EmailTag, EmailTo
from email_rules.exporting._templates import _JinjaTemplate
from email_rules.exporting.type_defs import RenderedRuleAction, RenderedRuleFilter


class ActionTag(_JinjaTemplate):
    tag_name: EmailTag


class FilterSubjectEq(_JinjaTemplate):
    text: EmailSubject
    case_sensitive: bool


class FilterToEq(_JinjaTemplate):
    text: EmailTo
    case_sensitive: bool


class FilterCombineAnd(_JinjaTemplate):
    expr_1: RenderedRuleFilter
    expr_2: RenderedRuleFilter


class FilterCombineNot(_JinjaTemplate):
    expr_1: RenderedRuleFilter


class FilterCombineOr(_JinjaTemplate):
    expr_1: RenderedRuleFilter
    expr_2: RenderedRuleFilter


class EmailRule(_JinjaTemplate):
    condition: RenderedRuleFilter
    actions: list[RenderedRuleAction]


class Templates:
    ACTION_TAG = ActionTag
    FILTER_COMBINE_AND = FilterCombineAnd
    FILTER_COMBINE_NOT = FilterCombineNot
    FILTER_COMBINE_OR = FilterCombineOr
    FILTER_SUBJECT_EQ = FilterSubjectEq
    FILTER_TO_EQ = FilterToEq
    EMAIL_RULE = EmailRule
