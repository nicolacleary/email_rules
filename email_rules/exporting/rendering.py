from itertools import chain
from pathlib import Path

from email_rules.rules import (
    RuleFromEq,
    RuleSubjectContains,
    RuleSubjectEq,
    RuleToEq,
    Rule,
    RuleAction,
    RuleFilter,
    AggregatedRuleFilter,
    NegatedRuleFilter,
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
)
from email_rules.rules._base_filters import GenericRuleTextEq, GenericRuleTextContains, GenericRuleTextListContains
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
        if isinstance(rule_action, RuleActionMarkAsRead):
            return RenderedRuleAction(r'addflag "\\Seen";')
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

    def get_rule_filter_extensions(self, rule_filter: RuleFilter) -> list[SieveExtension]:
        if type(rule_filter) is AggregatedRuleFilter:
            return list(chain(*[self.get_rule_filter_extensions(arg) for arg in rule_filter.args]))

        if type(rule_filter) is NegatedRuleFilter:
            return self.get_rule_filter_extensions(rule_filter.arg_1)

        if (
            isinstance(rule_filter, GenericRuleTextEq)
            or isinstance(rule_filter, GenericRuleTextContains)
            or isinstance(rule_filter, GenericRuleTextListContains)
        ):
            if rule_filter.case_sensitive:
                return [SieveExtension.COMPARATOR_ASCII_NUMERIC]
            return []

        raise ValueError(f"Unsupported type: {type(rule_filter)}")

    def get_rule_action_extensions(self, rule_action: RuleAction) -> list[SieveExtension]:
        if isinstance(rule_action, RuleActionStopProcessingAllFiles) or isinstance(
            rule_action, RuleActionStopProcessingCurrentFile
        ):
            return []
        if isinstance(rule_action, RuleActionAddTag) or isinstance(rule_action, RuleActionMoveToFolder):
            return [SieveExtension.FILEINTO]
        if isinstance(rule_action, RuleActionMarkAsRead):
            return [SieveExtension.IMAP4FLAGS]

        raise ValueError(f"Unsupported type: {type(rule_action)}")

    def get_rule_extension_requirements(self, rule: Rule) -> list[SieveExtension]:
        extensions = []
        extensions.extend(self.get_rule_filter_extensions(rule.filter_expr))
        for action in rule.actions:
            extensions.extend(self.get_rule_action_extensions(action))
        return extensions

    def get_extension_requirements(self, rules: list[Rule]) -> list[SieveExtension]:
        extensions: list[SieveExtension] = []
        for rule in rules:
            extensions.extend(self.get_rule_extension_requirements(rule))
        # Ensure we have include if it's there
        if extensions:
            extensions.append(SieveExtension.INCLUDE)
        return extensions

    def render_proton_email_rules_file_content(self, rules: list[Rule]) -> str:
        extensions = self.get_extension_requirements(rules)

        return Templates.PROTON_EMAIL_RULES_FILE(
            extensions=self.render_extensions(extensions),
            rendered_rules=[self.render_rule(rule) for rule in rules],
        ).render()

    def render_proton_email_rules_file(self, rules: list[Rule], file_path: Path) -> None:
        file_content = self.render_proton_email_rules_file_content(rules)
        with file_path.open("w") as f:
            f.write(file_content)
