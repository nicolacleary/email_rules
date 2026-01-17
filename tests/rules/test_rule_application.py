import pytest

from email_rules.core.type_defs import Email
from email_rules.rules.type_defs import Rule, RuleAction, RuleFilter
from email_rules.rules.basic_actions import RuleActionStopProcessingAllFiles, RuleActionStopProcessingCurrentFile

from tests.rules.common import ALWAYS_FALSE, ALWAYS_TRUE, RuleActionDoNothingAndTrackCalls


@pytest.fixture
def do_nothing_actions() -> list[RuleActionDoNothingAndTrackCalls]:
    RuleActionDoNothingAndTrackCalls.clear_calls()
    return [RuleActionDoNothingAndTrackCalls(instance=i) for i in range(3)]


def create_rule(
    action_order: list[int], filter_expr: RuleFilter, do_nothing_actions: list[RuleActionDoNothingAndTrackCalls]
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

    return Rule(filter_expr=filter_expr, actions=actions)


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
        Rule.apply_rules_to_email(generic_email, [rule])
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
        Rule.apply_rules_to_email(generic_email, [rule])
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
        Rule.apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == applied
