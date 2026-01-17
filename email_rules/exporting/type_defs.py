from enum import StrEnum
from typing import NewType


RenderedExtensions = NewType("RenderedExtensions", str)
RenderedRule = NewType("RenderedRule", str)
RenderedRuleAction = NewType("RenderedRuleAction", str)
RenderedRuleFilter = NewType("RenderedRuleFilter", str)


class FilterCombineOperation(StrEnum):
    AND = "allof"
    OR = "anyof"


class SieveComparisonOperator(StrEnum):
    EQ = "is"
    CONTAINS = "contains"


class SieveExtension(StrEnum):
    FILEINTO = "fileinto"
    INCLUDE = "include"
    ENVIRONMENT = "environment"
    VARIABLES = "variables"
    RELATIONAL = "relational"
    SPAMTEST = "spamtest"
    COMPARATOR_ASCII_NUMERIC = "comparator-i;ascii-numeric"
    IMAP4FLAGS = "imap4flags"


class SieveSectionName(StrEnum):
    ADDRESS = "address"
    HEADER = "header"


class SieveSectionPart(StrEnum):
    FROM = "from"
    SUBJECT = "subject"
    TO = "to"


class SieveSection(StrEnum):
    ADDRESS_FROM = "address_from"
    ADDRESS_TO = "address_to"
    HEADER_SUBJECT = "header_subject"

    @staticmethod
    def get_section_name_and_part(value: "SieveSection") -> tuple[SieveSectionName, SieveSectionPart]:
        name, part = value.value.split("_")
        return SieveSectionName[name.upper()], SieveSectionPart[part.upper()]
