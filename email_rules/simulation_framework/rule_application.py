from typing import Iterable, Sequence

from email_rules.core.type_defs import Email, EmailState
from email_rules.rules.type_defs import (
    Rule,
    RuleActionStopProcessingCurrentFileException,
    RuleActionStopProcessingAllFilesException,
)
from email_rules.simulation_framework.type_defs import RuleActionApplicationState, RuleApplication


def apply_rule_to_email(rule: Rule, email: Email, email_state: EmailState) -> Iterable[RuleApplication]:
    rule_application_state = RuleActionApplicationState.CONTINUE
    if not rule.filter_expr.evaluate(email):
        yield RuleApplication(
            email_state=email_state,
            rule_application_state=rule_application_state,
            current_rule=repr(rule),
            current_rule_applied=False,
            current_action=None,
        )
        return

    for action in rule.actions:
        if rule_application_state != RuleActionApplicationState.CONTINUE:
            break
        try:
            email_state = action.apply(email_state)
        except RuleActionStopProcessingCurrentFileException:
            rule_application_state = RuleActionApplicationState.STOP_PROCESSING_CURRENT_FILE
        except RuleActionStopProcessingAllFilesException:
            rule_application_state = RuleActionApplicationState.STOP_PROCESSING_ALL_FILES

        yield RuleApplication(
            email_state=email_state,
            rule_application_state=rule_application_state,
            current_rule=repr(rule),
            current_rule_applied=True,
            current_action=repr(action),
        )

    yield RuleApplication(
        email_state=email_state,
        rule_application_state=rule_application_state,
        current_rule=repr(rule),
        current_rule_applied=True,
        current_action=None,
    )


def apply_rules_to_email_iteratively(email: Email, rules: Sequence["Rule"]) -> Iterable[RuleApplication]:
    state = RuleApplication.create_initial_state()
    yield state

    for rule in rules:
        if state.rule_application_state != RuleActionApplicationState.CONTINUE:
            break

        for step in apply_rule_to_email(rule, email, state.email_state):
            yield step
            state = step


def apply_rules_to_email(email: Email, rules: Sequence["Rule"]) -> RuleApplication:
    if len(rules) == 0:
        return RuleApplication.create_initial_state()

    states = list(apply_rules_to_email_iteratively(email, rules))
    assert len(states) > 0, "We should always have the initial state at least"
    return states[-1]
