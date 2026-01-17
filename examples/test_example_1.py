import pytest

from email_rules.core.type_defs import Email, EmailAddress, EmailFrom, EmailSubject, EmailTo
from email_rules.simulation_framework.rule_simulation import EmailRuleSimulation

from example_1 import Folders, Tags, RULE_FILES


# Validating rule behaviour


class TestExample:
    @pytest.fixture
    def simulation(self) -> EmailRuleSimulation:
        return EmailRuleSimulation(
            folders=list(Folders.iterate_values()),
            tags=list(Tags.iterate_values()),
            rule_files=RULE_FILES,
        )

    def test_email_1(self, simulation: EmailRuleSimulation) -> None:
        email = Email(
            email_from=EmailFrom(EmailAddress("test@example.com")),
            email_to=[EmailTo(EmailAddress("email@example.com"))],
            email_subject=EmailSubject("Some Example Email"),
        )
        # Should pass
        simulation.assert_has_tag(email, Tags.SOME_TAG)
        # Should fail
        simulation.assert_is_moved_to(email, Folders.SOME_FOLDER)
