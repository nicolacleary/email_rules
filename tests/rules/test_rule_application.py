import pytest

from email_rules.core.type_defs import Email, EmailState
from email_rules.rules.type_defs import Rule


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
        rule.apply_rule_to_email(generic_email, EmailState.create_initial_state())
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
        rule.apply_rule_to_email(generic_email, EmailState.create_initial_state())
        assert RuleActionDoNothingAndTrackCalls.calls == []
