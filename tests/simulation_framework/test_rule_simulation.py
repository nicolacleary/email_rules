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
    def simulation(self) -> EmailRuleSimulation:
        # It's fine to just have rules that always apply here because rule application on email conditions
        # is tested per expression type elsewhere
        return EmailRuleSimulation(
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

    def test_is_moved_to_no_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        simulation.assert_is_moved_to(generic_email, Folders.PARENT_1)

    def test_is_moved_to_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        with pytest.raises(AssertionError, match="in parent_1, should be in parent_1/child_1"):
            simulation.assert_is_moved_to(generic_email, Folders.PARENT_1_CHILD_1)

    def test_has_tag_no_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        simulation.assert_has_tag(generic_email, Tags.TAG_1)

    def test_has_tag_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        with pytest.raises(AssertionError, match="not have tag TAG_2, tags: .'TAG_1'."):
            simulation.assert_has_tag(generic_email, Tags.TAG_2)

    def test_does_not_have_tag_no_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        simulation.assert_does_not_have_tag(generic_email, Tags.TAG_2)

    def test_does_not_have_tag_error(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        with pytest.raises(AssertionError, match="has tag TAG_1, tags: .'TAG_1'."):
            simulation.assert_does_not_have_tag(generic_email, Tags.TAG_1)

    def test_is_unread(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        simulation.assert_is_unread(generic_email)
        with pytest.raises(AssertionError, match="Email is unread"):
            simulation.assert_is_read(generic_email)

    def test_is_read(self, simulation: EmailRuleSimulation, generic_email: Email) -> None:
        simulation.rule_files[0].rules[0].actions.append(RuleActionMarkAsRead())
        simulation.assert_is_read(generic_email)
        with pytest.raises(AssertionError, match="Email is read"):
            simulation.assert_is_unread(generic_email)


class TestEmailRuleSimulationValidation:
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
        EmailRuleSimulation(
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
            EmailRuleSimulation(
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
        EmailRuleSimulation(
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
            EmailRuleSimulation(
                folders=list(Folders.iterate_values()),
                tags=list(Tags.iterate_values()),
                rule_files=[RuleFile(file_name="rule_file_1", rules=rules)],
            )
