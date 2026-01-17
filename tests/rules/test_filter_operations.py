import pytest

from email_rules.core import Email
from email_rules.rules import RuleFilter

from tests.rules.common import ALWAYS_FALSE, ALWAYS_TRUE


class TestCombination:
    def test_sanity_always_true(self, generic_email: Email) -> None:
        assert ALWAYS_TRUE.evaluate(generic_email)

    def test_sanity_always_false(self, generic_email: Email) -> None:
        assert not ALWAYS_FALSE.evaluate(generic_email)

    @pytest.mark.parametrize(
        "rule, expected_eval",
        [
            pytest.param(~ALWAYS_TRUE, False, id="not_true"),
            pytest.param(~ALWAYS_FALSE, True, id="not_false"),
        ],
    )
    def test_negation(self, rule: RuleFilter, expected_eval: bool, generic_email: Email) -> None:
        assert rule.evaluate(generic_email) == expected_eval

    @pytest.mark.parametrize(
        "rule, expected_eval",
        [
            pytest.param(ALWAYS_TRUE & ALWAYS_TRUE, True, id="true_and_true"),
            pytest.param(ALWAYS_TRUE & ALWAYS_FALSE, False, id="true_and_false"),
            pytest.param(ALWAYS_FALSE & ALWAYS_TRUE, False, id="false_and_true"),
            pytest.param(ALWAYS_FALSE & ALWAYS_FALSE, False, id="false_and_false"),
        ],
    )
    def test_and(self, rule: RuleFilter, expected_eval: bool, generic_email: Email) -> None:
        assert rule.evaluate(generic_email) == expected_eval

    @pytest.mark.parametrize(
        "rule, expected_eval",
        [
            pytest.param(ALWAYS_TRUE | ALWAYS_TRUE, True, id="true_or_true"),
            pytest.param(ALWAYS_TRUE | ALWAYS_FALSE, True, id="true_or_false"),
            pytest.param(ALWAYS_FALSE | ALWAYS_TRUE, True, id="false_or_true"),
            pytest.param(ALWAYS_FALSE | ALWAYS_FALSE, False, id="false_or_false"),
        ],
    )
    def test_or(self, rule: RuleFilter, expected_eval: bool, generic_email: Email) -> None:
        assert rule.evaluate(generic_email) == expected_eval

    @pytest.mark.parametrize(
        "rule, expected_eval",
        [
            pytest.param(ALWAYS_FALSE | (ALWAYS_TRUE & ALWAYS_TRUE), True),
            pytest.param(ALWAYS_FALSE & ALWAYS_TRUE | ALWAYS_TRUE, True),
            pytest.param(ALWAYS_FALSE & (ALWAYS_TRUE | ALWAYS_TRUE), False),
            pytest.param(~ALWAYS_FALSE & (ALWAYS_TRUE | ALWAYS_TRUE), True),
            pytest.param((~ALWAYS_FALSE) & (ALWAYS_TRUE | ALWAYS_TRUE), True),
            pytest.param(~ALWAYS_FALSE & ALWAYS_FALSE, False),
            pytest.param(~(ALWAYS_FALSE & ALWAYS_FALSE), True),
            pytest.param(~(ALWAYS_FALSE & ALWAYS_FALSE) & ALWAYS_FALSE, False),
        ],
    )
    def test_complex_combinations(self, rule: RuleFilter, expected_eval: bool, generic_email: Email) -> None:
        assert rule.evaluate(generic_email) == expected_eval

    @pytest.mark.parametrize(
        "rule_filter, expected_repr",
        [
            pytest.param(
                ALWAYS_FALSE & ALWAYS_TRUE & ALWAYS_TRUE,
                "(FALSE & TRUE & TRUE)",
                id="combine_two_and",
            ),
            pytest.param(
                ALWAYS_FALSE | ALWAYS_TRUE | ALWAYS_TRUE,
                "(FALSE | TRUE | TRUE)",
                id="combine_two_or",
            ),
            # Note that & has precedence over |
            pytest.param(
                ALWAYS_FALSE | ALWAYS_TRUE & ALWAYS_TRUE,
                "(FALSE | (TRUE & TRUE))",
                id="combine_or_then_and",
            ),
            pytest.param(
                ALWAYS_FALSE & ALWAYS_TRUE | ALWAYS_TRUE & ALWAYS_FALSE,
                "((FALSE & TRUE) | (TRUE & FALSE))",
                id="combine_three_operations_no_simplification",
            ),
            pytest.param(
                ALWAYS_FALSE | ALWAYS_TRUE & ALWAYS_TRUE & ALWAYS_FALSE,
                "(FALSE | (TRUE & TRUE & FALSE))",
                id="combine_three_operations_simplified",
            ),
            pytest.param(
                ~ALWAYS_FALSE,
                "~FALSE",
                id="not_false",
            ),
            pytest.param(
                ~ALWAYS_TRUE,
                "~TRUE",
                id="not_true",
            ),
            pytest.param(
                ~(ALWAYS_TRUE | ALWAYS_FALSE),
                "~(TRUE | FALSE)",
                id="not_true_or_false",
            ),
            pytest.param(
                ~(ALWAYS_TRUE | ALWAYS_FALSE) & ALWAYS_FALSE,
                "(~(TRUE | FALSE) & FALSE)",
                id="not_true_or_false_and_false",
            ),
        ],
    )
    def test_combination_structure(self, rule_filter: RuleFilter, expected_repr: str) -> None:
        assert repr(rule_filter) == expected_repr
