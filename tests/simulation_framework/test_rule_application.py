from typing import Sequence

import pytest

from email_rules.core import Email, EmailState
from email_rules.rules import (
    Rule,
    RuleAction,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
    RuleFilter,
)
from email_rules.simulation_framework import (
    RuleApplicationInterruptState,
    RuleApplicationState,
    RuleFile,
    RuleFileApplicationState,
    apply_rule_files_to_email_iteratively,
    apply_rules_to_email,
    apply_rules_to_email_iteratively,
    display_rule_file_application_states,
)
from tests.rules.common import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    RuleActionDoNothingAndTrackCalls,
)

RuleInfo = tuple[list[int], RuleFilter]


@pytest.fixture
def do_nothing_actions() -> list[RuleActionDoNothingAndTrackCalls]:
    RuleActionDoNothingAndTrackCalls.clear_calls()
    return [RuleActionDoNothingAndTrackCalls(instance=i) for i in range(3)]


def create_rule(
    action_order: Sequence[int],
    filter_expr: RuleFilter,
    do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
    comment: str | None = None,
) -> Rule:
    actions: list[RuleAction] = []
    for i in action_order:
        match i:
            case -1:
                actions.append(RuleActionStopProcessingAllFiles())
            case -2:
                actions.append(RuleActionStopProcessingCurrentFile())
            case _:
                actions.append(do_nothing_actions[i])

    return Rule(filter_expr=filter_expr, actions=actions, comment=comment)


def create_rules(
    rule_info: Sequence[RuleInfo], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls]
) -> Sequence[Rule]:
    return [
        create_rule(action_order, filter_expr, do_nothing_actions, comment=f"rule_{i}")
        for i, (action_order, filter_expr) in enumerate(rule_info)
    ]


def create_rule_file(
    rule_info_for_files: Sequence[Sequence[RuleInfo]], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls]
) -> Sequence[RuleFile]:
    return [
        RuleFile(
            file_name=f"file_{i}",
            rules=list(create_rules(rule_info, do_nothing_actions)),
        )
        for i, rule_info in enumerate(rule_info_for_files)
    ]


class TestApply:
    @pytest.mark.parametrize(
        "action_order",
        [
            pytest.param([], id="empty"),
            pytest.param([0], id="apply_1"),
            pytest.param([0, 1], id="apply_2"),
            pytest.param([0, 1, 2], id="apply_3"),
            pytest.param([2, 1, 0], id="apply_3_reverse"),
            pytest.param([2, 2], id="apply_duplicate"),
        ],
    )
    def test_order(
        self, action_order: list[int], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls], generic_email: Email
    ) -> None:
        rule = create_rule(action_order, ALWAYS_TRUE, do_nothing_actions)
        apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == action_order

    @pytest.mark.parametrize(
        "action_order",
        [
            pytest.param([], id="empty"),
            pytest.param([0], id="apply_1"),
            pytest.param([0, 1], id="apply_2"),
            pytest.param([0, 1, 2], id="apply_3"),
            pytest.param([2, 1, 0], id="apply_3_reverse"),
            pytest.param([2, 2], id="apply_duplicate"),
        ],
    )
    def test_does_not_apply_when_expression_is_false(
        self, action_order: list[int], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls], generic_email: Email
    ) -> None:
        rule = create_rule(action_order, ALWAYS_FALSE, do_nothing_actions)
        apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == []

    @pytest.mark.parametrize(
        "interrupt_action",
        [
            pytest.param(
                -1,
                id="all_files",
            ),
            pytest.param(
                -2,
                id="current_file",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "action_order, applied",
        [
            pytest.param([-1, 0], [], id="stop_before_apply_1"),
            pytest.param([0, -1], [0], id="apply_1"),
            pytest.param([-1, 0, 1], [], id="stop_before_apply_2"),
            pytest.param([0, 1, -1], [0, 1], id="apply_2"),
            pytest.param([0, -1, 1], [0], id="apply_1_then_stop"),
        ],
    )
    def test_interrupt(
        self,
        interrupt_action: int,
        action_order: list[int],
        applied: list[int],
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
        generic_email: Email,
    ) -> None:
        action_order = [i if i != -1 else interrupt_action for i in action_order]
        rule = create_rule(action_order, ALWAYS_TRUE, do_nothing_actions)
        apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == applied

    @pytest.mark.parametrize(
        "action_orders, applied",
        [
            pytest.param([], [], id="no_rules"),
            pytest.param([[0], [1]], [0, 1], id="apply_two"),
            pytest.param([[0], [-1], [1]], [0], id="stop_all_files_after_first"),
            pytest.param([[0], [-2], [1]], [0], id="stop_current_file_after_first"),
        ],
    )
    def test_interrupt_multiple_rules(
        self,
        action_orders: list[list[int]],
        applied: list[int],
        generic_email: Email,
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
    ) -> None:
        rule_info = [(action_order, ALWAYS_TRUE) for action_order in action_orders]
        rules = create_rules(rule_info, do_nothing_actions)
        apply_rules_to_email(generic_email, rules)
        assert RuleActionDoNothingAndTrackCalls.calls == applied

    @pytest.mark.parametrize(
        "rule_info, expected_states",
        [
            pytest.param([], [RuleApplicationState.create_initial_state()], id="empty"),
            pytest.param(
                [
                    ([], ALWAYS_TRUE),
                ],
                [
                    RuleApplicationState.create_initial_state(),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                ],
                id="one_rule_no_actions",
            ),
            pytest.param(
                [
                    ([1], ALWAYS_TRUE),
                ],
                [
                    RuleApplicationState.create_initial_state(),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                ],
                id="one_rule_one_action",
            ),
            pytest.param(
                [
                    ([0, 1, 2], ALWAYS_TRUE),
                    ([2, 1, 0], ALWAYS_FALSE),
                ],
                [
                    RuleApplicationState.create_initial_state(),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_0",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_2",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_1 filter_expr=FALSE, actions=[DO_NOTHING_2, DO_NOTHING_1, DO_NOTHING_0]>",
                        current_rule_applied=False,
                        current_action=None,
                    ),
                ],
                id="two_rules_multiple_actions_skip_second",
            ),
            pytest.param(
                [
                    ([0], ALWAYS_TRUE),
                    ([1, -1, 1], ALWAYS_TRUE),
                    ([2], ALWAYS_TRUE),
                ],
                [
                    RuleApplicationState.create_initial_state(),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_0",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                        current_rule="<rule_1 filter_expr=TRUE, actions=[DO_NOTHING_1, STOP_ALL_FILES, DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES,
                        current_rule="<rule_1 filter_expr=TRUE, actions=[DO_NOTHING_1, STOP_ALL_FILES, DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="STOP_ALL_FILES",
                    ),
                    RuleApplicationState(
                        email_state=EmailState.create_initial_state(),
                        rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES,
                        current_rule="<rule_1 filter_expr=TRUE, actions=[DO_NOTHING_1, STOP_ALL_FILES, DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                ],
                id="three_rules_end_after_second",
            ),
        ],
    )
    def test_iterative_application(
        self,
        rule_info: list[RuleInfo],
        expected_states: list[RuleApplicationState],
        generic_email: Email,
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
    ) -> None:
        rules = create_rules(rule_info, do_nothing_actions)
        all_states = list(apply_rules_to_email_iteratively(generic_email, rules))
        assert all_states == expected_states

    @pytest.mark.parametrize(
        "rule_info_for_files, expected_states",
        [
            pytest.param([], [RuleFileApplicationState.create_initial_state()], id="empty"),
            pytest.param(
                [
                    [([], ALWAYS_TRUE)],
                ],
                [
                    RuleFileApplicationState.create_initial_state(),
                    RuleFileApplicationState(
                        current_file_name="file_0",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                ],
                id="one_file_one_rule_no_actions",
            ),
            pytest.param(
                [
                    [([1], ALWAYS_TRUE)],
                ],
                [
                    RuleFileApplicationState.create_initial_state(),
                    RuleFileApplicationState(
                        current_file_name="file_0",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                                current_rule_applied=True,
                                current_action="DO_NOTHING_1",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                ],
                id="one_rule_file_one_rule_one_action",
            ),
            pytest.param(
                [
                    [([0, 1, 2], ALWAYS_TRUE)],
                    [([2, 1, 0], ALWAYS_FALSE)],
                ],
                [
                    RuleFileApplicationState.create_initial_state(),
                    RuleFileApplicationState(
                        current_file_name="file_0",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",  # noqa: E501
                                current_rule_applied=True,
                                current_action="DO_NOTHING_0",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",  # noqa: E501
                                current_rule_applied=True,
                                current_action="DO_NOTHING_1",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",  # noqa: E501
                                current_rule_applied=True,
                                current_action="DO_NOTHING_2",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",  # noqa: E501
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                    RuleFileApplicationState(
                        current_file_name="file_1",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=FALSE, actions=[DO_NOTHING_2, DO_NOTHING_1, DO_NOTHING_0]>",  # noqa: E501
                                current_rule_applied=False,
                                current_action=None,
                            ),
                        ],
                    ),
                ],
                id="two_files_two_rules_multiple_actions_skip_second",
            ),
            pytest.param(
                [
                    [([-1, 0], ALWAYS_TRUE)],
                    [([1], ALWAYS_TRUE)],
                    [([2], ALWAYS_TRUE)],
                ],
                [
                    RuleFileApplicationState.create_initial_state(),
                    RuleFileApplicationState(
                        current_file_name="file_0",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES,  # noqa: E501
                                current_rule="<rule_0 filter_expr=TRUE, actions=[STOP_ALL_FILES, DO_NOTHING_0]>",
                                current_rule_applied=True,
                                current_action="STOP_ALL_FILES",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_ALL_FILES,  # noqa: E501
                                current_rule="<rule_0 filter_expr=TRUE, actions=[STOP_ALL_FILES, DO_NOTHING_0]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                ],
                id="three_files_stop_all_after_first",
            ),
            pytest.param(
                [
                    [([-2, 0], ALWAYS_TRUE)],
                    [([1], ALWAYS_TRUE)],
                    [([2], ALWAYS_TRUE)],
                ],
                [
                    RuleFileApplicationState.create_initial_state(),
                    RuleFileApplicationState(
                        current_file_name="file_0",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_CURRENT_FILE,  # noqa: E501
                                current_rule="<rule_0 filter_expr=TRUE, actions=[STOP_CURRENT_FILE, DO_NOTHING_0]>",
                                current_rule_applied=True,
                                current_action="STOP_CURRENT_FILE",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.STOP_PROCESSING_CURRENT_FILE,  # noqa: E501
                                current_rule="<rule_0 filter_expr=TRUE, actions=[STOP_CURRENT_FILE, DO_NOTHING_0]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                    RuleFileApplicationState(
                        current_file_name="file_1",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                                current_rule_applied=True,
                                current_action="DO_NOTHING_1",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                    RuleFileApplicationState(
                        current_file_name="file_2",
                        rule_application_state_history=[
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_2]>",
                                current_rule_applied=True,
                                current_action="DO_NOTHING_2",
                            ),
                            RuleApplicationState(
                                email_state=EmailState.create_initial_state(),
                                rule_application_interrupt_state=RuleApplicationInterruptState.CONTINUE,
                                current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_2]>",
                                current_rule_applied=True,
                                current_action=None,
                            ),
                        ],
                    ),
                ],
                id="three_files_stop_first_but_continue",
            ),
        ],
    )
    def test_iterative_application_with_rule_files(
        self,
        rule_info_for_files: list[list[RuleInfo]],
        expected_states: list[RuleFileApplicationState],
        generic_email: Email,
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
    ) -> None:
        rule_files = create_rule_file(rule_info_for_files, do_nothing_actions)
        all_states = list(apply_rule_files_to_email_iteratively(generic_email, rule_files))

        assert display_rule_file_application_states(expected_states) == display_rule_file_application_states(all_states)
