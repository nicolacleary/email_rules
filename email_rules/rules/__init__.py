from email_rules.rules.basic_actions import (
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingCurrentFile,
    RuleActionStopProcessingAllFiles,
)
from email_rules.rules.basic_filters import (
    RuleFromEq,
    RuleSubjectContains,
    RuleSubjectEq,
    RuleToEq,
)
from email_rules.rules.type_defs import (
    AggregatedRuleFilter,
    NegatedRuleFilter,
    Rule,
    RuleAction,
    RuleActionApplicationException,
    RuleActionStopProcessingAllFilesException,
    RuleActionStopProcessingCurrentFileException,
    RuleFilter,
)


__all__ = (
    # basic_actions.py
    "RuleActionAddTag",
    "RuleActionMarkAsRead",
    "RuleActionMoveToFolder",
    "RuleActionStopProcessingCurrentFile",
    "RuleActionStopProcessingAllFiles",
    # basic_filters.py
    "RuleFromEq",
    "RuleSubjectContains",
    "RuleSubjectEq",
    "RuleToEq",
    # type_defs.py
    "AggregatedRuleFilter",
    "NegatedRuleFilter",
    "Rule",
    "RuleAction",
    "RuleActionApplicationException",
    "RuleActionStopProcessingAllFilesException",
    "RuleActionStopProcessingCurrentFileException",
    "RuleFilter",
)
