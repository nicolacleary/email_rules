from pathlib import PurePosixPath
from types import TracebackType
from typing import Generic, Iterable, Self, TypeVar, cast

from pydantic import BaseModel, model_validator

from email_rules.core import Email, EmailFolder, EmailState, EmailTag
from email_rules.rules import (
    Rule,
    RuleAction,
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
)
from email_rules.simulation_framework.rule_application import (
    apply_rule_files_to_email_iteratively,
    display_rule_file_application_states,
)
from email_rules.simulation_framework.type_defs import (
    RuleFile,
    RuleFileApplicationState,
)

T = TypeVar("T")


class IterableClass(Generic[T]):
    @classmethod
    def iterate_values(cls) -> Iterable[T]:
        for key, value in cls.__dict__.items():
            if key.startswith("_"):
                continue
            yield cast(T, value)


class EmailAccountSettings(BaseModel):
    folders: list[EmailFolder]
    tags: list[EmailTag]
    rule_files: list[RuleFile]

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

    def get_email_state_after_filtering(self, email: Email) -> tuple[EmailState, list[RuleFileApplicationState]]:
        step_history = list(apply_rule_files_to_email_iteratively(email, self.rule_files))
        if len(step_history) == 0:
            raise ValueError("No email state - this is an issue with the rule application logic")
        return step_history[-1].last_rule_application_state.email_state, step_history


class EmailRuleSimulation(object):
    def __init__(self, inbox: EmailAccountSettings, email: Email, display_state_history: bool = True):
        final_email_state, email_state_history = inbox.get_email_state_after_filtering(email)
        self.final_email_state = final_email_state
        self.email_state_history = email_state_history
        self._failures: list[str] = []
        self.display_state_history = display_state_history

    def print_email_state_history(self) -> None:
        print("File\tRule and action")
        print()
        print(display_rule_file_application_states(self.email_state_history))

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if not self._failures:
            return None
        if self.display_state_history:
            self.print_email_state_history()
        raise AssertionError("; ".join(self._failures))

    def assert_email_state(self, condition: bool, failure_message: str) -> None:
        if not condition:
            self._failures.append(failure_message)

    def assert_is_moved_to(self, destination: EmailFolder) -> None:
        self.assert_email_state(
            self.final_email_state.current_folder == destination,
            f"Email is in {self.final_email_state.current_folder}, should be in {destination}",
        )

    def assert_has_tag(self, tag: EmailTag) -> None:
        self.assert_email_state(
            tag in self.final_email_state.tags,
            f"Email does not have tag {tag}, tags: {self.final_email_state.tags}",
        )

    def assert_does_not_have_tag(self, tag: EmailTag) -> None:
        self.assert_email_state(
            tag not in self.final_email_state.tags, f"Email has tag {tag}, tags: {self.final_email_state.tags}"
        )

    def assert_is_read(self) -> None:
        self.assert_email_state(self.final_email_state.is_read, "Email is unread")

    def assert_is_unread(self) -> None:
        self.assert_email_state(not self.final_email_state.is_read, "Email is read")
