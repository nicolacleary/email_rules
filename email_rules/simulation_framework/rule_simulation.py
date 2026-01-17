from pathlib import PurePosixPath
from typing import Generic, Iterable, Self, TypeVar, cast

from pydantic import BaseModel, model_validator

from email_rules.core.type_defs import Email, EmailFolder, EmailState, EmailTag
from email_rules.rules.type_defs import Rule, RuleAction
from email_rules.rules.basic_actions import (
    RuleActionAddTag,
    RuleActionMoveToFolder,
    RuleActionStopProcessingCurrentFile,
    RuleActionStopProcessingAllFiles,
    RuleActionMarkAsRead,
)
from email_rules.simulation_framework.type_defs import RuleFile
from email_rules.simulation_framework.rule_application import (
    apply_rule_files_to_email_iteratively,
    display_rule_file_application_states,
)


T = TypeVar("T")


class IterableClass(Generic[T]):
    @classmethod
    def iterate_values(cls) -> Iterable[T]:
        for key, value in cls.__dict__.items():
            if key.startswith("_"):
                continue
            yield cast(T, value)


class EmailRuleSimulation(BaseModel):
    folders: list[EmailFolder]
    tags: list[EmailTag]
    rule_files: list[RuleFile]

    def _get_last_email_state(self, email: Email) -> EmailState:
        step_history = list(apply_rule_files_to_email_iteratively(email, self.rule_files))
        # The expected usecase is in pytest so I think it's fine to output to stdout for now
        print(display_rule_file_application_states(step_history))
        if len(step_history) == 0:
            raise ValueError("No email state - this is an issue with the rule application logic")
        return step_history[-1].last_rule_application_state.email_state

    def assert_is_moved_to(self, email: Email, destination: EmailFolder) -> None:
        final_email_state = self._get_last_email_state(email)
        assert final_email_state.current_folder == destination, (
            f"Email is in {final_email_state.current_folder}, should be in {destination}"
        )

    def assert_has_tag(self, email: Email, tag: EmailTag) -> None:
        final_email_state = self._get_last_email_state(email)
        assert tag in final_email_state.tags, f"Email does not have tag {tag}, tags: {final_email_state.tags}"

    def assert_does_not_have_tag(self, email: Email, tag: EmailTag) -> None:
        final_email_state = self._get_last_email_state(email)
        assert tag not in final_email_state.tags, f"Email has tag {tag}, tags: {final_email_state.tags}"

    def assert_is_read(self, email: Email) -> None:
        final_email_state = self._get_last_email_state(email)
        assert final_email_state.is_read, "Email is unread"

    def assert_is_unread(self, email: Email) -> None:
        final_email_state = self._get_last_email_state(email)
        assert not final_email_state.is_read, "Email is read"

    @model_validator(mode="after")
    def check_parent_folders_exist(self) -> Self:
        missing_folders: list[EmailFolder] = []
        for folder in self.folders:
            if folder.parent not in self.folders and folder.parent != EmailFolder(PurePosixPath(".")):
                missing_folders.append(folder.parent)

        if missing_folders:
            raise ValueError(f"Missing parent folders: {', '.join(str(parent) for parent in missing_folders)}")
        return self

    @model_validator(mode="after")
    def validate_rules(self) -> Self:
        errors = []

        for rule_file in self.rule_files:
            for rule in rule_file.rules:
                errors.extend(self.validate_rule(rule))

        if errors:
            raise ValueError(",".join(errors))
        return self

    def validate_rule(self, rule: Rule) -> list[str]:
        errors = []
        errors.extend(self.validate_actions(rule.actions))
        return [f"{rule}: {error}" for error in errors]

    def validate_actions(self, rule_actions: list[RuleAction]) -> list[str]:
        errors = []
        further_actions_unreachable = False
        for rule_action in rule_actions:
            if error_msg := self.validate_action(rule_action):
                errors.append(error_msg)

            if further_actions_unreachable:
                errors.append(f"Unreachable action {rule_action}")
            if isinstance(rule_action, RuleActionStopProcessingCurrentFile) or isinstance(
                rule_action, RuleActionStopProcessingAllFiles
            ):
                further_actions_unreachable = True
        return errors

    def validate_action(self, rule_action: RuleAction) -> str | None:
        if isinstance(rule_action, RuleActionAddTag):
            if rule_action.tag_to_apply not in self.tags:
                return f"Tag not found {rule_action.tag_to_apply}"
        elif isinstance(rule_action, RuleActionMoveToFolder):
            if rule_action.folder not in self.folders:
                return f"Folder not found {rule_action.folder}"
        elif (
            isinstance(rule_action, RuleActionStopProcessingCurrentFile)
            or isinstance(rule_action, RuleActionStopProcessingAllFiles)
            or isinstance(rule_action, RuleActionMarkAsRead)
        ):
            pass
        else:
            # E.g. if I were to add a custom action then it would not be validated at all
            return f"Cannot validate action (unhandled) {rule_action}"
        return None
