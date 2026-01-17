from typing import Iterable, Sequence

from email_rules.core.type_defs import Email, EmailState
from email_rules.rules.type_defs import (
    Rule,
    RuleActionStopProcessingCurrentFileException,
    RuleActionStopProcessingAllFilesException,
)
from email_rules.simulation_framework.type_defs import RuleApplicationInterruptState, RuleApplicationState


def apply_rule_to_email(rule: Rule, email: Email, email_state: EmailState) -> Iterable[RuleApplicationState]:
    rule_application_interrupt_state = RuleApplicationInterruptState.CONTINUE
    if not rule.filter_expr.evaluate(email):
        yield RuleApplicationState(
            email_state=email_state,
            rule_application_interrupt_state=rule_application_interrupt_state,
            current_rule=repr(rule),
            current_rule_applied=False,
            current_action=None,
        )
        return

    for action in rule.actions:
        if rule_application_interrupt_state != RuleApplicationInterruptState.CONTINUE:
            break
        try:
            email_state = action.apply(email_state)
        except RuleActionStopProcessingCurrentFileException:
            rule_application_interrupt_state = RuleApplicationInterruptState.STOP_PROCESSING_CURRENT_FILE
        except RuleActionStopProcessingAllFilesException:
            rule_application_interrupt_state = RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES

        yield RuleApplicationState(
            email_state=email_state,
            rule_application_interrupt_state=rule_application_interrupt_state,
            current_rule=repr(rule),
            current_rule_applied=True,
            current_action=repr(action),
        )

    yield RuleApplicationState(
        email_state=email_state,
        rule_application_interrupt_state=rule_application_interrupt_state,
        current_rule=repr(rule),
        current_rule_applied=True,
        current_action=None,
    )


def apply_rules_to_email_iteratively(email: Email, rules: Sequence["Rule"]) -> Iterable[RuleApplicationState]:
    current_state = RuleApplicationState.create_initial_state()
    yield current_state

    for rule in rules:
        if current_state.rule_application_interrupt_state != RuleApplicationInterruptState.CONTINUE:
            break

        for state_after_action in apply_rule_to_email(rule, email, current_state.email_state):
            yield state_after_action
            current_state = state_after_action


def apply_rules_to_email(email: Email, rules: Sequence["Rule"]) -> RuleApplicationState:
    if len(rules) == 0:
        return RuleApplicationState.create_initial_state()

    states = list(apply_rules_to_email_iteratively(email, rules))
    assert len(states) > 0, "We should always have the initial state at least"
    return states[-1]
