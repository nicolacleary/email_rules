import pytest
from example_1 import EMAIL_ACCOUNT_SETTINGS as EXAMPLE_1_ACCOUNT_SETTINGS
from example_1 import Folders as EXAMPLE_1_FOLDERS
from example_1 import Tags as EXAMPLE_1_TAGS

from email_rules.core import Email, EmailAddress, EmailFrom, EmailSubject, EmailTo
from email_rules.simulation_framework import EmailRuleSimulation

# Validating rule behaviour


class TestExample1:
    @pytest.fixture
    def email(self) -> Email:
        return Email(
            email_from=EmailFrom(EmailAddress("test@example.com")),
            email_to=[EmailTo(EmailAddress("email@example.com"))],
            email_subject=EmailSubject("Some Example Email"),
        )

    def test_tagging(self, email: Email) -> None:
        email.email_from = EmailFrom(EmailAddress("other-address@example.com"))
        with EmailRuleSimulation(inbox=EXAMPLE_1_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_has_tag(EXAMPLE_1_TAGS.SOME_TAG)

    def test_moving(self, email: Email) -> None:
        email.email_subject = EmailSubject("Won't be tagged")
        with EmailRuleSimulation(inbox=EXAMPLE_1_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_is_moved_to(EXAMPLE_1_FOLDERS.SOME_FOLDER)

    @pytest.mark.xfail(reason="The rule that adds the tag prevents further rules from being processed")
    def test_tagging_and_moving_same_email(self, email: Email) -> None:
        with EmailRuleSimulation(inbox=EXAMPLE_1_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_has_tag(EXAMPLE_1_TAGS.SOME_TAG)
            email_final_state.assert_is_moved_to(EXAMPLE_1_FOLDERS.SOME_FOLDER)
