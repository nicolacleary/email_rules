from pathlib import Path, PurePosixPath

import pytest

from email_rules.core.type_defs import EmailAddress, EmailFolder, EmailSubject, EmailTag, EmailTo
from email_rules.exporting._templates import _JinjaTemplate, _to_camel_case
from email_rules.exporting.templates import Templates
from email_rules.exporting.type_defs import RenderedRule, RenderedRuleAction, RenderedRuleFilter

from tests.exporting.common import TEST_DATA_TEMPLATES_DIR


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("nothing", "nothing"),
        pytest.param("somePhrase", "some_phrase"),
        pytest.param("SomePhrase", "some_phrase"),
        pytest.param("ALLCAPS", "allcaps"),
    ],
)
def test_to_camel_case(text: str, expected: str) -> None:
    assert _to_camel_case(text) == expected


@pytest.mark.parametrize(
    "template, expected_output",
    [
        pytest.param(
            Templates.ACTION_MOVE_TO_FOLDER(
                folder=EmailFolder(PurePosixPath("some/folder")),
            ),
            TEST_DATA_TEMPLATES_DIR / "action_move_to_folder.txt",
            id="action_move_to_folder",
        ),
        pytest.param(
            Templates.ACTION_TAG(
                tag_name=EmailTag("hi"),
            ),
            TEST_DATA_TEMPLATES_DIR / "action_tag.txt",
            id="action_tag",
        ),
        pytest.param(
            Templates.FILTER_SUBJECT_EQ(
                case_sensitive=False,
                text=EmailSubject("Some Text"),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_eq_case_insensitive.txt",
            id="filter_subject_eq_case_insensitive",
        ),
        pytest.param(
            Templates.FILTER_SUBJECT_EQ(
                case_sensitive=True,
                text=EmailSubject("Some Text"),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_subject_eq_case_sensitive.txt",
            id="filter_subject_eq_case_sensitive",
        ),
        pytest.param(
            Templates.FILTER_TO_EQ(
                case_sensitive=False,
                text=EmailTo(EmailAddress("Some Text")),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_to_eq_case_insensitive.txt",
            id="filter_to_eq_case_insensitive",
        ),
        pytest.param(
            Templates.FILTER_TO_EQ(
                case_sensitive=True,
                text=EmailTo(EmailAddress("Some Text")),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_to_eq_case_sensitive.txt",
            id="filter_to_eq_case_sensitive",
        ),
        pytest.param(
            Templates.FILTER_COMBINE_AND(
                expr_1=RenderedRuleFilter("abc"),
                expr_2=RenderedRuleFilter("def"),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_combine_and.txt",
            id="filter_combine_and",
        ),
        pytest.param(
            Templates.FILTER_COMBINE_NOT(
                expr_1=RenderedRuleFilter("abc"),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_combine_not.txt",
            id="filter_combine_not",
        ),
        pytest.param(
            Templates.FILTER_COMBINE_OR(
                expr_1=RenderedRuleFilter("abc"),
                expr_2=RenderedRuleFilter("def"),
            ),
            TEST_DATA_TEMPLATES_DIR / "filter_combine_or.txt",
            id="filter_combine_or",
        ),
        pytest.param(
            Templates.EMAIL_RULE(
                condition=RenderedRuleFilter('header :is "subject" "important"'),
                actions=[
                    RenderedRuleAction('fileinto "tag-1";'),
                    RenderedRuleAction('fileinto "tag-2";'),
                ],
            ),
            TEST_DATA_TEMPLATES_DIR / "rule_with_two_tags.txt",
            id="rule_with_two_tags",
        ),
        pytest.param(
            Templates.PROTON_EMAIL_RULES_FILE(
                rendered_rules=[
                    RenderedRule("some rule 1;"),
                    RenderedRule("some rule 2;"),
                ]
            ),
            TEST_DATA_TEMPLATES_DIR / "proton_email_rules_file.txt",
            id="proton_email_rules_file",
        ),
    ],
)
def test_render_templates(template: _JinjaTemplate, expected_output: Path) -> None:
    assert template.render() == expected_output.read_text()
