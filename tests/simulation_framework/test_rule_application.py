from typing import Sequence

import pytest

from email_rules.core.type_defs import Email, EmailState
from email_rules.rules.type_defs import Rule, RuleAction, RuleFilter
from email_rules.rules.basic_actions import RuleActionStopProcessingAllFiles, RuleActionStopProcessingCurrentFile
from email_rules.simulation_framework.type_defs import RuleActionApplicationState, RuleApplication
from email_rules.simulation_framework.rule_application import apply_rules_to_email, apply_rules_to_email_iteratively

from tests.rules.common import ALWAYS_FALSE, ALWAYS_TRUE, RuleActionDoNothingAndTrackCalls


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
            pytest.param([], [RuleApplication.create_initial_state()], id="empty"),
            pytest.param(
                [
                    ([], ALWAYS_TRUE),
                ],
                [
                    RuleApplication.create_initial_state(),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
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
                    RuleApplication.create_initial_state(),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
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
                    RuleApplication.create_initial_state(),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_0",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_2",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0, DO_NOTHING_1, DO_NOTHING_2]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
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
                    RuleApplication.create_initial_state(),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_0",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_0 filter_expr=TRUE, actions=[DO_NOTHING_0]>",
                        current_rule_applied=True,
                        current_action=None,
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.CONTINUE,
                        current_rule="<rule_1 filter_expr=TRUE, actions=[DO_NOTHING_1, STOP_ALL_FILES, DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="DO_NOTHING_1",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.STOP_PROCESSING_ALL_FILES,
                        current_rule="<rule_1 filter_expr=TRUE, actions=[DO_NOTHING_1, STOP_ALL_FILES, DO_NOTHING_1]>",
                        current_rule_applied=True,
                        current_action="STOP_ALL_FILES",
                    ),
                    RuleApplication(
                        email_state=EmailState.create_initial_state(),
                        rule_application_state=RuleActionApplicationState.STOP_PROCESSING_ALL_FILES,
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
        expected_states: list[RuleApplication],
        generic_email: Email,
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
    ) -> None:
        rules = create_rules(rule_info, do_nothing_actions)
        all_states = list(apply_rules_to_email_iteratively(generic_email, rules))
        assert all_states == expected_states
