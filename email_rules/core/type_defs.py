from pathlib import PurePosixPath
from typing import NewType, Self

from pydantic import BaseModel


EmailSubject = NewType("EmailSubject", str)
EmailAddress = NewType("EmailAddress", str)
EmailFrom = NewType("EmailFrom", EmailAddress)
EmailTo = NewType("EmailTo", EmailAddress)

EmailTag = NewType("EmailTag", str)
# Windows paths will give backslashes, which we don't want
EmailFolder = NewType("EmailFolder", PurePosixPath)


INBOX = EmailFolder(PurePosixPath("inbox"))


class Email(BaseModel):
    email_from: EmailFrom
    email_to: list[EmailTo]
    email_subject: EmailSubject


class EmailState(BaseModel):
    tags: set[EmailTag]
    current_folder: EmailFolder
    is_read: bool

    @classmethod
    def create_initial_state(cls) -> Self:
        return cls(
            tags=set(),
            current_folder=INBOX,
            is_read=False,
        )
