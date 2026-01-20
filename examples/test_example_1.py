import pytest
from example_1 import RULE_FILES, Folders, Tags

from email_rules.core import Email, EmailAddress, EmailFrom, EmailSubject, EmailTo
from email_rules.simulation_framework import EmailAccountSettings, EmailRuleSimulation

# Validating rule behaviour


class TestExample:
    @pytest.fixture
    def inbox_settings(self) -> EmailAccountSettings:
        return EmailAccountSettings(
            folders=list(Folders.iterate_values()),
            tags=list(Tags.iterate_values()),
            rule_files=RULE_FILES,
        )

    def test_email_1(self, inbox_settings: EmailAccountSettings) -> None:
        email = Email(
            email_from=EmailFrom(EmailAddress("test@example.com")),
            email_to=[EmailTo(EmailAddress("email@example.com"))],
            email_subject=EmailSubject("Some Example Email"),
        )

        with EmailRuleSimulation(inbox=inbox_settings, email=email) as email_final_state:
            email_final_state.assert_has_tag(Tags.SOME_TAG)
            # Should fail
            email_final_state.assert_is_moved_to(Folders.SOME_FOLDER)
