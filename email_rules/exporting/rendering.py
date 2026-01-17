from email_rules.rules.basic_filters import RuleSubjectEq, RuleToEq
from email_rules.rules.type_defs import RuleFilter, AggregatedRuleFilter, NegatedRuleFilter
from email_rules.exporting.templates import Templates
from email_rules.exporting.type_defs import RenderedRuleFilter


def render_rule_filter(rule_filter: RuleFilter) -> RenderedRuleFilter:
    if type(rule_filter) is AggregatedRuleFilter and rule_filter.is_operator_and():
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_AND(
                expr_1=render_rule_filter(rule_filter.arg_1),
                expr_2=render_rule_filter(rule_filter.arg_2),
            ).render()
        )
    elif type(rule_filter) is AggregatedRuleFilter:
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_OR(
                expr_1=render_rule_filter(rule_filter.arg_1),
                expr_2=render_rule_filter(rule_filter.arg_2),
            ).render()
        )

    if type(rule_filter) is NegatedRuleFilter:
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_NOT(
                expr_1=render_rule_filter(rule_filter.arg_1),
            ).render()
        )

    if type(rule_filter) is RuleSubjectEq:
        return RenderedRuleFilter(
            Templates.FILTER_SUBJECT_EQ(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
            ).render()
        )

    if type(rule_filter) is RuleToEq:
        return RenderedRuleFilter(
            Templates.FILTER_TO_EQ(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
            ).render()
        )

    raise ValueError(f"Unsupported type: {type(rule_filter)}")
