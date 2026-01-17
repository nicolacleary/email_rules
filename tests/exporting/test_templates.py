from pathlib import Path

import pytest

from email_rules.core.type_defs import EmailTag
from email_rules.exporting._templates import _JinjaTemplate, _to_camel_case
from email_rules.exporting.templates import Templates


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
        (
            Templates.ACTION_TAG(
                tag_name=EmailTag("hi"),
            ),
            TEST_DATA_TEMPLATES_DIR / "action_tag.txt",
        ),
    ],
)
def test_render_templates(template: _JinjaTemplate, expected_output: Path) -> None:
    assert template.render() == expected_output.read_text()
