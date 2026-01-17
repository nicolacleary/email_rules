import pytest

from email_rules.core.type_defs import Email
from email_rules.rules.type_defs import Rule, RuleAction
from email_rules.rules.basic_actions import RuleActionStopProcessingAllFiles, RuleActionStopProcessingCurrentFile

from tests.rules.common import ALWAYS_FALSE, ALWAYS_TRUE, RuleActionDoNothingAndTrackCalls


@pytest.fixture
def do_nothing_actions() -> list[RuleActionDoNothingAndTrackCalls]:
    RuleActionDoNothingAndTrackCalls.clear_calls()
    return [RuleActionDoNothingAndTrackCalls(instance=i) for i in range(3)]


class TestApply:
    @pytest.mark.parametrize(
        "order",
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
        self, order: list[int], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls], generic_email: Email
    ) -> None:
        rule = Rule(
            filter_expr=ALWAYS_TRUE,
            actions=[do_nothing_actions[i] for i in order],
        )
        Rule.apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == order

    @pytest.mark.parametrize(
        "order",
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
        self, order: list[int], do_nothing_actions: list[RuleActionDoNothingAndTrackCalls], generic_email: Email
    ) -> None:
        rule = Rule(
            filter_expr=ALWAYS_FALSE,
            actions=[do_nothing_actions[i] for i in order],
        )
        Rule.apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == []

    @pytest.mark.parametrize(
        "interrupt_action",
        [
            pytest.param(
                RuleActionStopProcessingAllFiles(),
                id="all_files",
            ),
            pytest.param(
                RuleActionStopProcessingCurrentFile(),
                id="current_file",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "order, applied",
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
        interrupt_action: RuleAction,
        order: list[int],
        applied: list[int],
        do_nothing_actions: list[RuleActionDoNothingAndTrackCalls],
        generic_email: Email,
    ) -> None:
        rule = Rule(
            filter_expr=ALWAYS_TRUE,
            actions=[do_nothing_actions[i] if i != -1 else interrupt_action for i in order],
        )
        Rule.apply_rules_to_email(generic_email, [rule])
        assert RuleActionDoNothingAndTrackCalls.calls == applied
