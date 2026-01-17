from enum import StrEnum
from typing import NewType


RenderedRule = NewType("RenderedRule", str)
RenderedRuleAction = NewType("RenderedRuleAction", str)
RenderedRuleFilter = NewType("RenderedRuleFilter", str)


class SieveComparisonOperator(StrEnum):
    EQ = "is"
    CONTAINS = "contains"


class SieveSectionName(StrEnum):
    ADDRESS = "address"


class SieveSectionPart(StrEnum):
    FROM = "from"


class SieveSection(StrEnum):
    ADDRESS_FROM = "address_from"

    @staticmethod
    def get_section_name_and_part(value: "SieveSection") -> tuple[SieveSectionName, SieveSectionPart]:
        name, part = value.value.split("_")
        return SieveSectionName[name.upper()], SieveSectionPart[part.upper()]
