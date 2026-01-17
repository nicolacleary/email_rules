import pytest

from email_rules.core.type_defs import Email


@pytest.fixture
def generic_email() -> Email:
    return Email()
