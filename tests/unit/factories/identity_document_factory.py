from datetime import date

from customer_management.domain.subscriber.identity_document import (
    DocumentType,
    IdentityDocument,
)
from tests.unit.factories.constants import FIXED_DATE_OF_BIRTH


class IdentityDocumentFactory:
    @staticmethod
    def create(
        *,
        document_number: str = "AA1234567",
        document_type: DocumentType = DocumentType.NATIONAL_ID,
        first_name: str = "Ayla",
        last_name: str = "Mammadova",
        date_of_birth: date = FIXED_DATE_OF_BIRTH,
        citizenship: str = "AZ",
    ) -> IdentityDocument:
        return IdentityDocument(
            document_number=document_number,
            document_type=document_type,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            citizenship=citizenship,
        )
