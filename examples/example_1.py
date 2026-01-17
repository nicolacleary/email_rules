from pathlib import Path, PurePosixPath

from email_rules.core.type_defs import Email, EmailAddress, EmailFolder, EmailFrom, EmailTag, EmailSubject
from email_rules.rules.type_defs import Rule, RuleFilter
from email_rules.rules.basic_actions import (
    RuleActionAddTag,
    RuleActionMoveToFolder,
    RuleActionStopProcessingCurrentFile,
)
from email_rules.rules.basic_filters import RuleFromEq, RuleSubjectContains
from email_rules.exporting.rendering import SieveRenderer
from email_rules.exporting.type_defs import RenderedRuleFilter, SieveExtension
from email_rules.simulation_framework.type_defs import RuleFile
from email_rules.simulation_framework.rule_simulation import IterableClass


OUTPUT_FOLDER = Path(__file__).parent.parent / "z_output"


# Custom actions, filters, etc.


class SpamTestFilter(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        # Spam values aren't modelled in email state
        return False


# Defining Rules


class Folders(IterableClass[EmailFolder]):
    SOME_FOLDER = EmailFolder(PurePosixPath("some_folder"))


class Tags(IterableClass[EmailTag]):
    SOME_TAG = EmailTag("SOME_TAG")


RULE_FILES = [
    RuleFile(
        file_name="some_rules_file.txt",
        rules=[
            Rule(
                comment="Generated: Do not run this script on spam messages",
                filter_expr=SpamTestFilter(),
                actions=[
                    RuleActionStopProcessingCurrentFile(),
                ],
            ),
            Rule(
                comment="Tag anything with 'example' in the subject",
                filter_expr=RuleSubjectContains(
                    text=EmailSubject("example"),
                ),
                actions=[
                    RuleActionAddTag(tag_to_apply=Tags.SOME_TAG),
                    RuleActionStopProcessingCurrentFile(),
                ],
            ),
            Rule(
                comment="Move anything from test@example.com to folder",
                filter_expr=RuleFromEq(
                    text=EmailFrom(EmailAddress("test@example.com")),
                ),
                actions=[RuleActionMoveToFolder(folder=Folders.SOME_FOLDER)],
            ),
        ],
    )
]


# Rendering


class CustomSieveRenderer(SieveRenderer):
    def get_rule_filter_extensions(self, rule_filter: RuleFilter) -> list[SieveExtension]:
        if isinstance(rule_filter, SpamTestFilter):
            return [
                SieveExtension.SPAMTEST,
                SieveExtension.COMPARATOR_ASCII_NUMERIC,
                SieveExtension.RELATIONAL,
            ]
        return super().get_rule_filter_extensions(rule_filter)

    def render_rule_filter(self, rule_filter: RuleFilter) -> RenderedRuleFilter:
        if type(rule_filter) is SpamTestFilter:
            return RenderedRuleFilter('spamtest :value "ge" :comparator "i;ascii-numeric" "${1}"')
        return super().render_rule_filter(rule_filter)


# TODO - move RuleFile definition so this can be a function in the rendering
def render_rule_file(renderer: SieveRenderer, rule_file: RuleFile, output_folder: Path) -> None:
    renderer.render_proton_email_rules_file(rule_file.rules, output_folder / rule_file.file_name)


if __name__ == "__main__":
    renderer = CustomSieveRenderer()
    for rule_file in RULE_FILES:
        render_rule_file(renderer, rule_file, OUTPUT_FOLDER)
