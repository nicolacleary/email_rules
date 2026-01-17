from email_rules.rules.basic_actions import (
    RuleActionAddTag,
    RuleActionMoveToFolder,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
)
from email_rules.rules.basic_filters import RuleFromEq, RuleSubjectContains, RuleSubjectEq, RuleToEq
from email_rules.rules.type_defs import Rule, RuleAction, RuleFilter, AggregatedRuleFilter, NegatedRuleFilter
from email_rules.exporting.templates import Templates
from email_rules.exporting.type_defs import (
    FilterCombineOperation,
    RenderedRule,
    RenderedRuleAction,
    RenderedRuleFilter,
    SieveComparisonOperator,
    SieveSection,
)


def render_rule_action(rule_action: RuleAction) -> RenderedRuleAction:
    if type(rule_action) is RuleActionAddTag:
        return RenderedRuleAction(
            Templates.ACTION_TAG(
                tag_name=rule_action.tag_to_apply,
            ).render()
        )
    if type(rule_action) is RuleActionMoveToFolder:
        return RenderedRuleAction(
            Templates.ACTION_MOVE_TO_FOLDER(
                folder=rule_action.folder,
            ).render()
        )
    if type(rule_action) is RuleActionStopProcessingAllFiles:
        return RenderedRuleAction("stop;")
    if type(rule_action) is RuleActionStopProcessingCurrentFile:
        return RenderedRuleAction("return;")

    raise ValueError(f"Unsupported type: {type(rule_action)}")


def render_rule_filter(rule_filter: RuleFilter) -> RenderedRuleFilter:
    if type(rule_filter) is AggregatedRuleFilter and rule_filter.is_operator_and():
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_AND_OR(
                exprs=[render_rule_filter(arg) for arg in rule_filter.args],
                operation=FilterCombineOperation.AND,
            ).render()
        )
    elif type(rule_filter) is AggregatedRuleFilter:
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_AND_OR(
                exprs=[render_rule_filter(arg) for arg in rule_filter.args],
                operation=FilterCombineOperation.OR,
            ).render()
        )

    if type(rule_filter) is NegatedRuleFilter:
        return RenderedRuleFilter(
            Templates.FILTER_COMBINE_NOT(
                expr_1=render_rule_filter(rule_filter.arg_1),
            ).render()
        )

    if type(rule_filter) is RuleFromEq:
        section_name, section_part = SieveSection.get_section_name_and_part(SieveSection.ADDRESS_FROM)
        return RenderedRuleFilter(
            Templates.FILTER_GENERIC(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
                operation=SieveComparisonOperator.EQ,
                section_name=section_name,
                section_part=section_part,
            ).render()
        )

    if type(rule_filter) is RuleSubjectContains:
        section_name, section_part = SieveSection.get_section_name_and_part(SieveSection.HEADER_SUBJECT)
        return RenderedRuleFilter(
            Templates.FILTER_GENERIC(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
                operation=SieveComparisonOperator.CONTAINS,
                section_name=section_name,
                section_part=section_part,
            ).render()
        )

    if type(rule_filter) is RuleSubjectEq:
        section_name, section_part = SieveSection.get_section_name_and_part(SieveSection.HEADER_SUBJECT)
        return RenderedRuleFilter(
            Templates.FILTER_GENERIC(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
                operation=SieveComparisonOperator.EQ,
                section_name=section_name,
                section_part=section_part,
            ).render()
        )

    if type(rule_filter) is RuleToEq:
        section_name, section_part = SieveSection.get_section_name_and_part(SieveSection.ADDRESS_TO)
        return RenderedRuleFilter(
            Templates.FILTER_GENERIC(
                text=rule_filter.text,
                case_sensitive=rule_filter.case_sensitive,
                operation=SieveComparisonOperator.EQ,
                section_name=section_name,
                section_part=section_part,
            ).render()
        )

    raise ValueError(f"Unsupported type: {type(rule_filter)}")


def render_rule(rule: Rule) -> RenderedRule:
    return RenderedRule(
        Templates.EMAIL_RULE(
            comment=rule.comment,
            condition=render_rule_filter(rule.filter_expr),
            actions=[render_rule_action(action) for action in rule.actions],
        ).render()
    )


def render_proton_email_rules_file(rules: list[Rule]) -> str:
    return Templates.PROTON_EMAIL_RULES_FILE(rendered_rules=[render_rule(rule) for rule in rules]).render()
