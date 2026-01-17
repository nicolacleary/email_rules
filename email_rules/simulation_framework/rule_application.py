from typing import Iterable, Sequence

from email_rules.core import Email, EmailState
from email_rules.rules import (
    Rule,
    RuleActionStopProcessingAllFilesException,
    RuleActionStopProcessingCurrentFileException,
)
from email_rules.simulation_framework.type_defs import (
    RuleApplicationInterruptState,
    RuleApplicationState,
    RuleFile,
    RuleFileApplicationState,
)


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


def apply_rules_to_email_iteratively(
    email: Email, rules: Sequence["Rule"], current_state: RuleApplicationState | None = None
) -> Iterable[RuleApplicationState]:
    current_state = RuleApplicationState.create_initial_state() if not current_state else current_state
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


def apply_rule_files_to_email_iteratively(
    email: Email, rule_files: Sequence[RuleFile]
) -> Iterable[RuleFileApplicationState]:
    current_file_state = RuleFileApplicationState.create_initial_state()
    yield current_file_state
    last_application_state = current_file_state.last_rule_application_state

    for rule_file in rule_files:
        # We yield the initial state above, so there is no need to provide it again
        rule_application_state_history = list(
            apply_rules_to_email_iteratively(email, rule_file.rules, last_application_state)
        )[1:]

        current_file_state = RuleFileApplicationState(
            current_file_name=rule_file.file_name,
            rule_application_state_history=rule_application_state_history,
        )
        yield current_file_state
        last_application_state = current_file_state.last_rule_application_state

        if (
            last_application_state.rule_application_interrupt_state
            == RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES
        ):
            break
        last_application_state = RuleApplicationState(
            email_state=last_application_state.email_state,
            rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
            current_rule=None,
            current_rule_applied=False,
            current_action=None,
        )


def display_rule_file_application_states(file_states: list[RuleFileApplicationState]) -> str:
    lines = []

    for file_state in file_states:
        lines.append(str(file_state.current_file_name))
        for rule_application_state in file_state.rule_application_state_history:
            lines.append(
                "".join(
                    [
                        "\t",
                        "current_rule=" + str(rule_application_state.current_rule),
                        " current_rule_applied=" + str(rule_application_state.current_rule_applied),
                        " current_action=" + str(rule_application_state.current_action),
                        " interrupt_state=" + str(rule_application_state.rule_application_interrupt_state),
                    ]
                )
            )

    return "\n".join(lines)
