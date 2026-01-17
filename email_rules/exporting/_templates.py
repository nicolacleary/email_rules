from abc import ABC
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "static/templates"
assert _TEMPLATE_DIR.exists(), f"Could not find {_TEMPLATE_DIR}"


_TEMPLATE_LOADER = FileSystemLoader(searchpath=_TEMPLATE_DIR)
_TEMPLATE_ENV = Environment(loader=_TEMPLATE_LOADER)


def _to_camel_case(text: str) -> str:
    if text.isupper():
        return text.lower()

    reformatted_text = ""
    for char in text:
        if reformatted_text and char.isupper():
            reformatted_text += "_"
        reformatted_text += char.lower()

    return reformatted_text


class _JinjaTemplate(BaseModel, ABC):
    def template_name(self) -> str:
        return f"{_to_camel_case(self.__class__.__name__)}.j2"

    @property
    def template(self) -> Template:
        return _TEMPLATE_ENV.get_template(self.template_name())

    def args(self) -> dict[str, Any]:
        return self.model_dump()

    def render(self) -> str:
        return self.template.render(self.args())
