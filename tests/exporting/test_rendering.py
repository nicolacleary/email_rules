from pathlib import Path, PurePosixPath

import pytest

from email_rules.core import (
    EmailAddress,
    EmailFolder,
    EmailFrom,
    EmailSubject,
    EmailTag,
    EmailTo,
)
from email_rules.exporting import SieveExtension, SieveRenderer
from email_rules.rules import (
    Rule,
    RuleAction,
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
    RuleFilter,
    RuleFromEq,
    RuleSubjectContains,
    RuleSubjectEq,
    RuleToEq,
)
from tests.exporting.common import TEST_DATA_TEMPLATES_DIR


@pytest.mark.parametrize(
    "action, expected_output",
    [
        pytest.param(
            (RuleActionAddTag(tag_to_apply=EmailTag("hi"))),
            TEST_DATA_TEMPLATES_DIR / "action_tag.txt",
            id="action_tag",
        ),
        pytest.param(
            (RuleActionMarkAsRead()),
            'addflag "\\\\Seen";',
            id="mark_as_read",
        ),
    ],
)
def test_render_rule_action(action: RuleAction, expected_output: Path | str) -> None:
    expected_output_str = expected_output.read_text() if isinstance(expected_output, Path) else expected_output
    # Just a placeholder to test the function, since this should be a 1-1 rendering
    assert SieveRenderer().render_rule_action(action) == expected_output_str


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
    assert SieveRenderer().render_rule_filter(rule) == expected_output.read_text()


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
    assert SieveRenderer().render_rule(rule) == expected_output.read_text()


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
    assert SieveRenderer().render_extensions(dependencies) == expected


@pytest.mark.parametrize(
    "rule_action, expected",
    [
        pytest.param(
            RuleActionAddTag(tag_to_apply=EmailTag("some_tag")),
            [SieveExtension.FILEINTO],
            id="add_tag",
        ),
        pytest.param(
            RuleActionMarkAsRead(),
            [SieveExtension.IMAP4FLAGS],
            id="mark_as_read",
        ),
        pytest.param(
            RuleActionMoveToFolder(folder=EmailFolder(PurePosixPath("some_folder"))),
            [SieveExtension.FILEINTO],
            id="move_to_folder",
        ),
        pytest.param(
            RuleActionStopProcessingAllFiles(),
            [],
            id="stop_processing_all_files",
        ),
        pytest.param(
            RuleActionStopProcessingCurrentFile(),
            [],
            id="stop_processing_current_file",
        ),
    ],
)
def test_get_rule_action_extensions(rule_action: RuleAction, expected: list[SieveExtension]) -> None:
    assert SieveRenderer().get_rule_action_extensions(rule_action) == expected
