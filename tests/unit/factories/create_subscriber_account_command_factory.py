from customer_management.application.subscriber.commands.create_subscriber_account.command import (
    CreateSubscriberAccountCommand,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from tests.unit.factories.constants import FIXED_APPLICATION_DATE


class CreateSubscriberAccountCommandFactory:
    @staticmethod
    def create(
        subscriber_id: Id[Subscriber], **overrides
    ) -> CreateSubscriberAccountCommand:
        values = {
            "subscriber_id": subscriber_id,
            "service_address_id": "address-002",
            "city_code": "BAK",
            "street_code": "NIZ",
            "building_code": "12",
            "apartment_code": "35",
            "application_date": FIXED_APPLICATION_DATE,
        }
        values.update(overrides)
        return CreateSubscriberAccountCommand(**values)
