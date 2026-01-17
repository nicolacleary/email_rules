import pytest

from email_rules.core import Email
from email_rules.rules import RuleSubjectContains, RuleSubjectEq, RuleToEq


class TestRuleTextContains:
    @pytest.mark.parametrize(
        "text, case_sensitive, expected",
        [
            pytest.param("Sub", True, True, id="case_right"),
            pytest.param("Sub", False, True, id="case_right_and_insensitive"),
            pytest.param("sub", True, False, id="case_wrong"),
            pytest.param("sub", False, True, id="case_wrong_but_insensitive"),
        ],
    )
    def test_subject_contains(self, text: str, case_sensitive: bool, expected: bool, generic_email: Email) -> None:
        assert RuleSubjectContains.create(text, case_sensitive).evaluate(generic_email) == expected


class TestRuleTextEq:
    @pytest.mark.parametrize(
        "text, case_sensitive, expected",
        [
            pytest.param("Subject 1", True, True, id="case_right"),
            pytest.param("Subject 1", False, True, id="case_right_and_insensitive"),
            pytest.param("subject 1", True, False, id="case_wrong"),
            pytest.param("subject 1", False, True, id="case_wrong_but_insensitive"),
        ],
    )
    def test_subject_eq(self, text: str, case_sensitive: bool, expected: bool, generic_email: Email) -> None:
        assert RuleSubjectEq.create(text, case_sensitive).evaluate(generic_email) == expected


class TestRuleTextListContains:
    @pytest.mark.parametrize(
        "text, case_sensitive, expected",
        [
            pytest.param("to_1@example.com", True, True, id="case_right"),
            pytest.param("to_1@example.com", False, True, id="case_right_and_insensitive"),
            pytest.param("TO_1@example.com", True, False, id="case_wrong"),
            pytest.param("TO_1@example.com", False, True, id="case_wrong_but_insensitive"),
            pytest.param("to_2@example.com", True, True, id="other_recipient"),
            pytest.param("not_sent_to@example.com", True, False, id="not_sent_to"),
        ],
    )
    def test_rule_to_eq(self, text: str, case_sensitive: bool, expected: bool, generic_email: Email) -> None:
        assert RuleToEq.create(text, case_sensitive).evaluate(generic_email) == expected
