from pathlib import Path

import pytest

from email_rules.core.type_defs import EmailAddress, EmailSubject, EmailTag, EmailTo
from email_rules.exporting._templates import _JinjaTemplate, _to_camel_case
from email_rules.exporting.templates import Templates
from email_rules.exporting.type_defs import RenderedRuleFilter


TEST_DATA_DIR = Path(__file__).parent.parent / "data"
TEST_DATA_TEMPLATES_DIR = TEST_DATA_DIR / "templates"


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
    ],
)
def test_render_templates(template: _JinjaTemplate, expected_output: Path) -> None:
    assert template.render() == expected_output.read_text()
