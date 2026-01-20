from pathlib import Path, PurePosixPath

from email_rules.core import (
    EmailFolder,
    EmailSubject,
    EmailTag,
)
from email_rules.exporting import SieveRenderer
from email_rules.rules import (
    Rule,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingCurrentFile,
    RuleSubjectContains,
)
from email_rules.simulation_framework import (
    EmailAccountSettings,
    IterableClass,
    RuleFile,
)

OUTPUT_FOLDER = Path(__file__).parent.parent / "z_output"


# Defining Rules


class Folders(IterableClass[EmailFolder]):
    FEEDBACK_ETC = EmailFolder(PurePosixPath("feedback_etc"))


class Tags(IterableClass[EmailTag]):
    pass


RULE_FILES = [
    RuleFile(
        file_name="example_1.txt",
        rules=[
            Rule(
                comment="Filter out emails asking for feedback, reviews, etc.",
                filter_expr=(
                    RuleSubjectContains(
                        text=EmailSubject("your feedback is important to us"),
                    )
                    | RuleSubjectContains(
                        text=EmailSubject("Please tell us about your experience"),
                    )
                ),
                actions=[
                    RuleActionMoveToFolder(folder=Folders.FEEDBACK_ETC),
                    RuleActionMarkAsRead(),
                    RuleActionStopProcessingCurrentFile(),
                ],
            )
        ],
    )
]


EMAIL_ACCOUNT_SETTINGS = EmailAccountSettings(
    folders=list(Folders.iterate_values()),
    tags=list(Tags.iterate_values()),
    rule_files=RULE_FILES,
)


# Rendering


# TODO - move RuleFile definition so this can be a function in the rendering
def render_rule_file(renderer: SieveRenderer, rule_file: RuleFile, output_folder: Path) -> None:
    renderer.render_proton_email_rules_file(rule_file.rules, output_folder / rule_file.file_name)


if __name__ == "__main__":
    renderer = SieveRenderer()
    for rule_file in RULE_FILES:
        render_rule_file(renderer, rule_file, OUTPUT_FOLDER)
