from typing import Self

from pydantic import model_validator

from email_rules.core.type_defs import EmailFolder, EmailTag
from email_rules.exporting._templates import _JinjaTemplate
from email_rules.exporting.type_defs import (
    FilterCombineOperation,
    RenderedExtensions,
    RenderedRule,
    RenderedRuleAction,
    RenderedRuleFilter,
    SieveComparisonOperator,
    SieveSectionName,
    SieveSectionPart,
)


class ActionMoveToFolder(_JinjaTemplate):
    folder: EmailFolder


class ActionTag(_JinjaTemplate):
    tag_name: EmailTag


class FilterGeneric(_JinjaTemplate):
    text: str
    case_sensitive: bool
    operation: SieveComparisonOperator
    section_name: SieveSectionName
    section_part: SieveSectionPart


class FilterCombineAndOr(_JinjaTemplate):
    operation: FilterCombineOperation
    exprs: list[RenderedRuleFilter]

    @model_validator(mode="after")
    def validate_num_expressions(self) -> Self:
        if len(self.exprs) < 2:
            raise ValueError(f"Number of expressions should be at least 2, got: {self.exprs}")
        return self


class FilterCombineNot(_JinjaTemplate):
    expr_1: RenderedRuleFilter


class EmailRule(_JinjaTemplate):
    comment: str | None
    condition: RenderedRuleFilter
    actions: list[RenderedRuleAction]


class ProtonEmailRulesFile(_JinjaTemplate):
    extensions: RenderedExtensions | None
    rendered_rules: list[RenderedRule]


class Templates:
    ACTION_MOVE_TO_FOLDER = ActionMoveToFolder
    ACTION_TAG = ActionTag
    FILTER_COMBINE_AND_OR = FilterCombineAndOr
    FILTER_COMBINE_NOT = FilterCombineNot
    FILTER_GENERIC = FilterGeneric
    EMAIL_RULE = EmailRule
    PROTON_EMAIL_RULES_FILE = ProtonEmailRulesFile
