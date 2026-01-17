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
    RenderedExtensions,
    RenderedRule,
    RenderedRuleAction,
    RenderedRuleFilter,
    SieveComparisonOperator,
    SieveExtension,
    SieveSection,
)


class SieveRenderer:
    def render_rule_action(self, rule_action: RuleAction) -> RenderedRuleAction:
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

    def render_extensions(self, dependencies: list[SieveExtension]) -> RenderedExtensions | None:
        # Enforce unique and in alphabetical order
        # TODO: check later to see if import order is important
        dependencies = sorted(list(set(dependencies)))

        if len(dependencies) == 0:
            return None
        if len(dependencies) == 1:
            return RenderedExtensions(f'require "{dependencies[0]}";')

        deps_as_str = ", ".join([f'"{dep.value}"' for dep in dependencies])

        return RenderedExtensions(f"require [{deps_as_str}];")

    def render_rule_filter(self, rule_filter: RuleFilter) -> RenderedRuleFilter:
        if type(rule_filter) is AggregatedRuleFilter and rule_filter.is_operator_and():
            return RenderedRuleFilter(
                Templates.FILTER_COMBINE_AND_OR(
                    exprs=[self.render_rule_filter(arg) for arg in rule_filter.args],
                    operation=FilterCombineOperation.AND,
                ).render()
            )
        elif type(rule_filter) is AggregatedRuleFilter:
            return RenderedRuleFilter(
                Templates.FILTER_COMBINE_AND_OR(
                    exprs=[self.render_rule_filter(arg) for arg in rule_filter.args],
                    operation=FilterCombineOperation.OR,
                ).render()
            )

        if type(rule_filter) is NegatedRuleFilter:
            return RenderedRuleFilter(
                Templates.FILTER_COMBINE_NOT(
                    expr_1=self.render_rule_filter(rule_filter.arg_1),
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

    def render_rule(self, rule: Rule) -> RenderedRule:
        return RenderedRule(
            Templates.EMAIL_RULE(
                comment=rule.comment,
                condition=self.render_rule_filter(rule.filter_expr),
                actions=[self.render_rule_action(action) for action in rule.actions],
            ).render()
        )

    def render_proton_email_rules_file(self, rules: list[Rule]) -> str:
        DEFAULT_EXTENSIONS = [
            SieveExtension.FILEINTO,
            SieveExtension.INCLUDE,
            SieveExtension.ENVIRONMENT,
            SieveExtension.VARIABLES,
            SieveExtension.RELATIONAL,
            SieveExtension.COMPARATOR_ASCII_NUMERIC,
            SieveExtension.SPAMTEST,
        ]
        rendered_extensions = self.render_extensions(DEFAULT_EXTENSIONS)

        return Templates.PROTON_EMAIL_RULES_FILE(
            extensions=rendered_extensions,
            rendered_rules=[self.render_rule(rule) for rule in rules],
        ).render()
