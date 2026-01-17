from email_rules.rules.basic_actions import RuleActionAddTag
from email_rules.rules.basic_filters import RuleSubjectEq, RuleToEq
from email_rules.rules.type_defs import Rule, RuleAction, RuleFilter, AggregatedRuleFilter, NegatedRuleFilter
from email_rules.exporting.templates import Templates
from email_rules.exporting.type_defs import RenderedRule, RenderedRuleAction, RenderedRuleFilter


def render_rule_action(rule_action: RuleAction) -> RenderedRuleAction:
    if type(rule_action) is RuleActionAddTag:
        return RenderedRuleAction(
            Templates.ACTION_TAG(
                tag_name=rule_action.tag_to_apply,
            ).render()
        )

    raise ValueError(f"Unsupported type: {type(rule_action)}")


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


def render_rule(rule: Rule) -> RenderedRule:
    return RenderedRule(
        Templates.EMAIL_RULE(
            condition=render_rule_filter(rule.filter_expr),
            actions=[render_rule_action(action) for action in rule.actions],
        ).render()
    )


def render_proton_email_rules_file(rules: list[Rule]) -> str:
    return Templates.PROTON_EMAIL_RULES_FILE(rendered_rules=[render_rule(rule) for rule in rules]).render()
