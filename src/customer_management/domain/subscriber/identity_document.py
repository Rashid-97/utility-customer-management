from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from customer_management.common.exceptions import InvalidDomainValueError


class DocumentType(str, Enum):
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"


@dataclass(frozen=True, slots=True)
class IdentityDocument:
    document_number: str
    document_type: DocumentType
    first_name: str
    last_name: str
    date_of_birth: date
    citizenship: str

    def __post_init__(self) -> None:
        text_fields = {
            "document_number": self.document_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "citizenship": self.citizenship,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                label = field_name.replace("_", " ").capitalize()
                raise InvalidDomainValueError(f"{label} must not be empty.")
            object.__setattr__(self, field_name, value.strip())

        if not isinstance(self.document_type, DocumentType):
            raise InvalidDomainValueError("Document type is invalid.")
        if not isinstance(self.date_of_birth, date):
            raise InvalidDomainValueError("Date of birth is invalid.")

