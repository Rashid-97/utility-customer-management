from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from customer_management.application.exceptions import ExternalServiceUnavailableError
from customer_management.application.ports.identity_verification import (
    IdentityVerificationPort,
)
from customer_management.domain.subscriber.identity_document import (
    DocumentType,
    IdentityDocument,
)


IdentityKey = tuple[DocumentType, str]


class MockIdentityVerificationAdapter(IdentityVerificationPort):
    OUTAGE_DOCUMENT_NUMBER = "IDENTITY-SERVICE-UNAVAILABLE"

    def __init__(
        self,
        records: Mapping[IdentityKey, IdentityDocument] | None = None,
    ) -> None:
        self._records = dict(records) if records is not None else _default_records()

    def verify_identity(
        self,
        document_type: DocumentType,
        document_number: str,
    ) -> IdentityDocument | None:
        normalized_number = document_number.strip()
        if normalized_number == self.OUTAGE_DOCUMENT_NUMBER:
            raise ExternalServiceUnavailableError("Identity")
        return self._records.get((document_type, normalized_number))


def _default_records() -> dict[IdentityKey, IdentityDocument]:
    records = (
        IdentityDocument(
            document_number="AZE-ADULT-001",
            document_type=DocumentType.NATIONAL_ID,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
            citizenship="AZ",
        ),
        IdentityDocument(
            document_number="FOREIGN-ADULT-001",
            document_type=DocumentType.PASSPORT,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 9, 20),
            citizenship="GE",
        ),
        IdentityDocument(
            document_number="AZE-MINOR-001",
            document_type=DocumentType.NATIONAL_ID,
            first_name="Michael",
            last_name="Brown",
            date_of_birth=date(2012, 3, 10),
            citizenship="AZ",
        ),
    )
    return {
        (record.document_type, record.document_number): record for record in records
    }

