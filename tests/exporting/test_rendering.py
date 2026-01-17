from pathlib import Path

import pytest

from email_rules.core.type_defs import EmailAddress, EmailFrom, EmailSubject, EmailTag, EmailTo
from email_rules.rules.basic_actions import RuleActionAddTag
from email_rules.rules.basic_filters import RuleFromEq, RuleSubjectContains, RuleSubjectEq, RuleToEq
from email_rules.rules.type_defs import Rule, RuleAction, RuleFilter
from email_rules.exporting.rendering import render_extensions, render_rule, render_rule_action, render_rule_filter
from email_rules.exporting.type_defs import SieveExtension

from tests.exporting.common import TEST_DATA_TEMPLATES_DIR


@pytest.mark.parametrize(
    "action, expected_output",
    [
        pytest.param(
            (RuleActionAddTag(tag_to_apply=EmailTag("hi"))),
            TEST_DATA_TEMPLATES_DIR / "action_tag.txt",
            id="action_tag",
        ),
    ],
)
def test_render_rule_action(action: RuleAction, expected_output: Path) -> None:
    # Just a placeholder to test the function, since this should be a 1-1 rendering
    assert render_rule_action(action) == expected_output.read_text()


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
        pytest.param(
            (RuleFromEq(text=EmailFrom(EmailAddress("Some Text")), case_sensitive=False)),
            TEST_DATA_TEMPLATES_DIR / "filter_from_eq_case_insensitive.txt",
            id="filter_from_eq_case_insensitive",
        ),
        pytest.param(
            (RuleSubjectEq(text=EmailSubject("Some Text"), case_sensitive=False)),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_eq_case_insensitive.txt",
            id="filter_subject_eq_case_insensitive",
        ),
        pytest.param(
            (RuleSubjectEq(text=EmailSubject("Some Text"), case_sensitive=True)),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_eq_case_sensitive.txt",
            id="filter_subject_eq_case_sensitive",
        ),
        pytest.param(
            (RuleSubjectContains(text=EmailSubject("Some Text"), case_sensitive=False)),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_contains_case_insensitive.txt",
            id="filter_subject_contains_case_insensitive",
        ),
        pytest.param(
            (RuleSubjectContains(text=EmailSubject("Some Text"), case_sensitive=True)),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_contains_case_sensitive.txt",
            id="filter_subject_contains_case_sensitive",
        ),
        pytest.param(
            (RuleToEq(text=EmailTo(EmailAddress("Some Text")), case_sensitive=False)),
            TEST_DATA_TEMPLATES_DIR / "filter_to_eq_case_insensitive.txt",
            id="filter_to_eq_case_insensitive",
        ),
        pytest.param(
            (RuleToEq(text=EmailTo(EmailAddress("Some Text")), case_sensitive=True)),
            TEST_DATA_TEMPLATES_DIR / "filter_to_eq_case_sensitive.txt",
            id="filter_to_eq_case_sensitive",
        ),
    ],
)
def test_render_rule_filter(rule: RuleFilter, expected_output: Path) -> None:
    assert render_rule_filter(rule) == expected_output.read_text()


@pytest.mark.parametrize(
    "rule, expected_output",
    [
        pytest.param(
            Rule(
                filter_expr=RuleSubjectEq(text=EmailSubject("IMPORTANT"), case_sensitive=False),
                actions=[
                    RuleActionAddTag(tag_to_apply=EmailTag("tag-1")),
                    RuleActionAddTag(tag_to_apply=EmailTag("tag-2")),
                ],
            ),
            TEST_DATA_TEMPLATES_DIR / "rule_with_two_tags.txt",
            id="rule_with_two_tags",
        ),
    ],
)
def test_render_rule(rule: Rule, expected_output: Path) -> None:
    assert render_rule(rule) == expected_output.read_text()


@pytest.mark.parametrize(
    "dependencies, expected",
    [
        pytest.param(
            [],
            None,
            id="no_dependencies",
        ),
        pytest.param(
            [SieveExtension.ENVIRONMENT],
            'require "environment";',
            id="one_dependency",
        ),
        pytest.param(
            [SieveExtension.ENVIRONMENT, SieveExtension.ENVIRONMENT],
            'require "environment";',
            id="duplicate_extension",
        ),
        pytest.param(
            [
                SieveExtension.FILEINTO,
                SieveExtension.ENVIRONMENT,
                SieveExtension.VARIABLES,
            ],
            'require ["environment", "fileinto", "variables"];',
            id="three_extensions",
        ),
    ],
)
def test_render_extensions(dependencies: list[SieveExtension], expected: str | None) -> None:
    assert render_extensions(dependencies) == expected
