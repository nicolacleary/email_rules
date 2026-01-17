from pathlib import Path

import pytest

from email_rules.core.type_defs import EmailAddress, EmailSubject, EmailTo
from email_rules.rules.basic_filters import RuleSubjectEq, RuleToEq
from email_rules.rules.type_defs import RuleFilter
from email_rules.exporting.rendering import render_rule_filter

from tests.exporting.common import TEST_DATA_TEMPLATES_DIR


@pytest.mark.parametrize(
    "rule, expected_output",
    [
        pytest.param(
            (
                ~RuleSubjectEq(text=EmailSubject("IMPORTANT"), case_sensitive=False)
                & (
                    RuleToEq(text=EmailTo(EmailAddress("abc@example.com")), case_sensitive=False)
                    | RuleToEq(text=EmailTo(EmailAddress("def@example.com")), case_sensitive=False)
                )
            ),
            TEST_DATA_TEMPLATES_DIR / "rule_filter_combinations_1.txt",
            id="rule_filter_combinations_1",
        ),
    ],
)
def test_render_rule_filter(rule: RuleFilter, expected_output: Path) -> None:
    assert render_rule_filter(rule) == expected_output.read_text()
