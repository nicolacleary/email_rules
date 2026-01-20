from pathlib import PurePosixPath

import pytest
from pydantic import ValidationError

from email_rules.core import Email, EmailFolder, EmailTag
from email_rules.rules import (
    Rule,
    RuleActionAddTag,
    RuleActionMarkAsRead,
    RuleActionMoveToFolder,
    RuleActionStopProcessingAllFiles,
    RuleActionStopProcessingCurrentFile,
    RuleFilter,
)
from email_rules.simulation_framework import (
    EmailAccountSettings,
    EmailRuleSimulation,
    IterableClass,
    RuleFile,
)


# TODO: consolidate with other definition
class RuleAlwaysTrue(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        return True

    def __repr__(self) -> str:
        return "TRUE"


class Folders(IterableClass[EmailFolder]):
    PARENT_1 = EmailFolder(PurePosixPath("parent_1"))
    PARENT_1_CHILD_1 = EmailFolder(PurePosixPath("parent_1/child_1"))


class Tags(IterableClass[EmailTag]):
    TAG_1 = EmailTag("TAG_1")
    TAG_2 = EmailTag("TAG_2")


ALWAYS_TRUE = RuleAlwaysTrue()
RULE_ADD_TAG_1 = Rule(filter_expr=ALWAYS_TRUE, actions=[RuleActionAddTag(tag_to_apply=Tags.TAG_1)])
RULE_MOVE_TO_PARENT_1 = Rule(filter_expr=ALWAYS_TRUE, actions=[RuleActionMoveToFolder(folder=Folders.PARENT_1)])


class TestIterableClass:
    def test_folders(self) -> None:
        assert list(Folders.iterate_values()) == [Folders.PARENT_1, Folders.PARENT_1_CHILD_1]

    def test_tags(self) -> None:
        assert list(Tags.iterate_values()) == [Tags.TAG_1, Tags.TAG_2]


class TestEmailRuleSimulationAssertFunctions:
    @pytest.fixture
    def inbox_settings(self) -> EmailAccountSettings:
        # It's fine to just have rules that always apply here because rule application on email conditions
        # is tested per expression type elsewhere
        return EmailAccountSettings(
            folders=list(Folders.iterate_values()),
            tags=list(Tags.iterate_values()),
            rule_files=[
                RuleFile(
                    file_name="rule_file_1",
                    rules=[
                        RULE_ADD_TAG_1,
                        RULE_MOVE_TO_PARENT_1,
                    ],
                )
            ],
        )

    def test_is_moved_to_no_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state:
            email_final_state.assert_is_moved_to(Folders.PARENT_1)

    def test_is_moved_to_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with (
            pytest.raises(AssertionError, match="in parent_1, should be in parent_1/child_1"),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_is_moved_to(Folders.PARENT_1_CHILD_1)

    def test_has_tag_no_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state:
            email_final_state.assert_has_tag(Tags.TAG_1)

    def test_has_tag_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with (
            pytest.raises(AssertionError, match="not have tag TAG_2, tags: .'TAG_1'."),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_has_tag(Tags.TAG_2)

    def test_does_not_have_tag_no_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state:
            email_final_state.assert_does_not_have_tag(Tags.TAG_2)

    def test_does_not_have_tag_error(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with (
            pytest.raises(AssertionError, match="has tag TAG_1, tags: .'TAG_1'."),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_does_not_have_tag(Tags.TAG_1)

    def test_is_unread(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        with EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state:
            email_final_state.assert_is_unread()
        with (
            pytest.raises(AssertionError, match="Email is unread"),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_is_read()

    def test_is_read(self, inbox_settings: EmailAccountSettings, generic_email: Email) -> None:
        inbox_settings.rule_files[0].rules[0].actions.append(RuleActionMarkAsRead())

        with EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state:
            email_final_state.assert_is_read()
        with (
            pytest.raises(AssertionError, match="Email is read"),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_is_unread()

    def test_assert_email_state_aggregates_errors(
        self, inbox_settings: EmailAccountSettings, generic_email: Email
    ) -> None:
        with (
            pytest.raises(AssertionError, match="error 1; error 3"),
            EmailRuleSimulation(inbox=inbox_settings, email=generic_email) as email_final_state,
        ):
            email_final_state.assert_email_state(False, "error 1")
            email_final_state.assert_email_state(True, "error 2")
            email_final_state.assert_email_state(False, "error 3")


class TestEmailAccountSettingsValidation:
    @pytest.mark.parametrize(
        "folders",
        [
            pytest.param([], id="empty"),
            pytest.param([Folders.PARENT_1], id="just_parent"),
            pytest.param([Folders.PARENT_1, Folders.PARENT_1_CHILD_1], id="parent_and_child"),
            pytest.param([Folders.PARENT_1_CHILD_1, Folders.PARENT_1], id="parent_and_child_reverse_order"),
        ],
    )
    def test_parent_folder_missing_no_errors(self, folders: list[EmailFolder]) -> None:
        EmailAccountSettings(
            folders=folders,
            tags=[],
            rule_files=[],
        )

    @pytest.mark.parametrize(
        "folders, error_msg",
        [
            pytest.param([Folders.PARENT_1_CHILD_1], f"Missing parent folders. {Folders.PARENT_1}", id="just_child"),
        ],
    )
    def test_parent_folder_missing_errors(self, folders: list[EmailFolder], error_msg: str) -> None:
        with pytest.raises(ValidationError, match=error_msg):
            EmailAccountSettings(
                folders=folders,
                tags=[],
                rule_files=[],
            )

    @pytest.mark.parametrize(
        "rules",
        [
            pytest.param([], id="empty"),
            pytest.param([Rule(filter_expr=ALWAYS_TRUE, actions=[])], id="no_actions"),
            pytest.param(
                [RULE_ADD_TAG_1],
                id="tag_exists",
            ),
            pytest.param(
                [RULE_MOVE_TO_PARENT_1],
                id="folder_exists",
            ),
            pytest.param(
                [Rule(filter_expr=ALWAYS_TRUE, actions=[RuleActionStopProcessingCurrentFile()])],
                id="stop_processing_file",
            ),
            pytest.param(
                [Rule(filter_expr=ALWAYS_TRUE, actions=[RuleActionStopProcessingAllFiles()])],
                id="stop_processing_all_files",
            ),
            pytest.param([Rule(filter_expr=ALWAYS_TRUE, actions=[RuleActionMarkAsRead()])], id="mark_as_read"),
        ],
    )
    def test_validate_rules_no_errors(self, rules: list[Rule]) -> None:
        EmailAccountSettings(
            folders=list(Folders.iterate_values()),
            tags=list(Tags.iterate_values()),
            rule_files=[RuleFile(file_name="rule_file_1", rules=rules)],
        )

    @pytest.mark.parametrize(
        "rules, error_msg",
        [
            pytest.param(
                [
                    Rule(
                        filter_expr=ALWAYS_TRUE,
                        actions=[RuleActionAddTag(tag_to_apply=EmailTag("I-do-not-exist"))],
                    )
                ],
                "Tag not found I-do-not-exist",
                id="tag_missing",
            ),
            pytest.param(
                [
                    Rule(
                        filter_expr=ALWAYS_TRUE,
                        actions=[RuleActionMoveToFolder(folder=EmailFolder(PurePosixPath("does_not_exist")))],
                    )
                ],
                "Folder not found does_not_exist",
                id="folder_missing",
            ),
            pytest.param(
                [
                    Rule(
                        filter_expr=ALWAYS_TRUE,
                        actions=[RuleActionStopProcessingCurrentFile(), RuleActionAddTag(tag_to_apply=Tags.TAG_1)],
                    ),
                ],
                "Unreachable action",
                id="action_after_stop_processing_file",
            ),
            pytest.param(
                [
                    Rule(
                        filter_expr=ALWAYS_TRUE,
                        actions=[RuleActionStopProcessingAllFiles(), RuleActionAddTag(tag_to_apply=Tags.TAG_1)],
                    ),
                ],
                "Unreachable action",
                id="action_after_stop_processing_all_files",
            ),
        ],
    )
    def test_validate_rules_errors(self, rules: list[Rule], error_msg: str) -> None:
        with pytest.raises(ValidationError, match=error_msg):
            EmailAccountSettings(
                folders=list(Folders.iterate_values()),
                tags=list(Tags.iterate_values()),
                rule_files=[RuleFile(file_name="rule_file_1", rules=rules)],
            )
