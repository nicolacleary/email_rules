import pytest

from pydantic import ValidationError

from email_rules.core import Email, EmailAddress, EmailFrom, EmailTo, EmailSubject


@pytest.fixture
def generic_email() -> Email:
    try:
        return Email(
            email_from=EmailFrom(EmailAddress("from@example.com")),
            email_to=[EmailTo(EmailAddress("to_1@example.com")), EmailTo(EmailAddress("to_2@example.com"))],
            email_subject=EmailSubject("Subject 1"),
        )
    except ValidationError as err:
        print(err.errors())
        raise err
