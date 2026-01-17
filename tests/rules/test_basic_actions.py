from pathlib import PurePosixPath

from email_rules.core import EmailFolder, EmailState, EmailTag
from email_rules.rules import (
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
)


def test_rule_action_add_tag() -> None:
    text = "some_tag"
    rule_action = RuleActionAddTag(
        tag_to_apply=EmailTag(text),
    )
    assert rule_action.apply(EmailState.create_initial_state()).tags == {
        EmailTag(text),
    }


def test_rule_action_move_to_folder() -> None:
    folder_path = PurePosixPath("abc/def")
    rule_action = RuleActionMoveToFolder(
        folder=EmailFolder(folder_path),
    )
    assert rule_action.apply(EmailState.create_initial_state()).current_folder == EmailFolder(folder_path)


def test_rule_action_mark_as_read() -> None:
    rule_action = RuleActionMarkAsRead()
    assert rule_action.apply(EmailState.create_initial_state()).is_read is True
