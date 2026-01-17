from email_rules.core.type_defs import EmailFolder, EmailState, EmailTag
from email_rules.rules.type_defs import (
    RuleAction,
    RuleActionStopProcessingAllFilesException,
    RuleActionStopProcessingCurrentFileException,
)


class RuleActionAddTag(RuleAction):
    tag_to_apply: EmailTag

    def apply(self, email_state: EmailState) -> EmailState:
        email_state.tags.add(self.tag_to_apply)
        return email_state


class RuleActionMoveToFolder(RuleAction):
    folder: EmailFolder

    def apply(self, email_state: EmailState) -> EmailState:
        email_state.current_folder = self.folder
        return email_state


class RuleActionStopProcessingCurrentFile(RuleAction):
    def apply(self, email_state: EmailState) -> EmailState:
        raise RuleActionStopProcessingCurrentFileException()


class RuleActionStopProcessingAllFiles(RuleAction):
    def apply(self, email_state: EmailState) -> EmailState:
        raise RuleActionStopProcessingAllFilesException()


class RuleActionMarkAsRead(RuleAction):
    def apply(self, email_state: EmailState) -> EmailState:
        email_state.is_read = True
        return email_state
