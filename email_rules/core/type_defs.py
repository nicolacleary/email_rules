from typing import NewType

from pydantic import BaseModel


EmailSubject = NewType("EmailSubject", str)
EmailAddress = NewType("EmailAddress", str)
EmailFrom = NewType("EmailFrom", EmailAddress)
EmailTo = NewType("EmailTo", EmailAddress)


class Email(BaseModel):
    email_from: EmailFrom
    email_to: list[EmailTo]
    email_subject: EmailSubject
