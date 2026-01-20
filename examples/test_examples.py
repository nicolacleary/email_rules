import pytest
from example_2 import EMAIL_ACCOUNT_SETTINGS as EXAMPLE_2_ACCOUNT_SETTINGS
from example_2 import Folders as EXAMPLE_2_FOLDERS
from example_2 import Tags as EXAMPLE_2_TAGS

from email_rules.core import Email, EmailAddress, EmailFrom, EmailSubject, EmailTo
from email_rules.simulation_framework import EmailRuleSimulation

# Validating rule behaviour


def create_email(
    email_from: EmailFrom | None = None,
    email_to: list[EmailTo] | None = None,
    email_subject: EmailSubject | None = None,
) -> Email:
    return Email(
        email_from=email_from or EmailFrom(EmailAddress("test@example.com")),
        email_to=email_to or [EmailTo(EmailAddress("email@example.com"))],
        email_subject=email_subject or EmailSubject("Some Example Email"),
    )


class TestExample2:
    def test_tagging(self) -> None:
        email = create_email(email_from=EmailFrom(EmailAddress("other-address@example.com")))
        with EmailRuleSimulation(inbox=EXAMPLE_2_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_has_tag(EXAMPLE_2_TAGS.SOME_TAG)

    def test_moving(self) -> None:
        email = create_email(email_subject=EmailSubject("Won't be tagged"))
        with EmailRuleSimulation(inbox=EXAMPLE_2_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_is_moved_to(EXAMPLE_2_FOLDERS.SOME_FOLDER)

    @pytest.mark.xfail(reason="The rule that adds the tag prevents further rules from being processed")
    def test_tagging_and_moving_same_email(self) -> None:
        email = create_email(
            email_from=EmailFrom(EmailAddress("other-address@example.com")),
            email_subject=EmailSubject("Won't be tagged"),
        )
        with EmailRuleSimulation(inbox=EXAMPLE_2_ACCOUNT_SETTINGS, email=email) as email_final_state:
            email_final_state.assert_has_tag(EXAMPLE_2_TAGS.SOME_TAG)
            email_final_state.assert_is_moved_to(EXAMPLE_2_FOLDERS.SOME_FOLDER)
