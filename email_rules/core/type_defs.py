from typing import NewType, Self

from pydantic import BaseModel


EmailSubject = NewType("EmailSubject", str)
EmailAddress = NewType("EmailAddress", str)
EmailFrom = NewType("EmailFrom", EmailAddress)
EmailTo = NewType("EmailTo", EmailAddress)

EmailTag = NewType("EmailTag", str)


class Email(BaseModel):
    email_from: EmailFrom
    email_to: list[EmailTo]
    email_subject: EmailSubject


class EmailState(BaseModel):
    tags: set[EmailTag]

    @classmethod
    def create_initial_state(cls) -> Self:
        return cls(
            tags=set(),
        )
