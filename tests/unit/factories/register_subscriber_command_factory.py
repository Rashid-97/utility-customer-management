from customer_management.application.subscriber.commands.register_subscriber.command import (
    RegisterSubscriberCommand,
)
from customer_management.domain.subscriber.identity_document import DocumentType
from tests.unit.factories.constants import FIXED_APPLICATION_DATE


class RegisterSubscriberCommandFactory:
    @staticmethod
    def create(**overrides) -> RegisterSubscriberCommand:
        values = {
            "document_number": "AA1234567",
            "document_type": DocumentType.NATIONAL_ID,
            "service_address_id": "address-002",
            "city_code": "BAK",
            "street_code": "NIZ",
            "building_code": "12",
            "apartment_code": "35",
            "application_date": FIXED_APPLICATION_DATE,
        }
        values.update(overrides)
        return RegisterSubscriberCommand(**values)
