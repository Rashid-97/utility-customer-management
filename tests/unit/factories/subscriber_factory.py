from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from tests.unit.factories.constants import FIXED_CREATED_AT
from tests.unit.factories.identity_document_factory import IdentityDocumentFactory
from tests.unit.factories.subscriber_code_factory import SubscriberCodeFactory


class SubscriberFactory:
    @staticmethod
    def create(*, with_account: bool = False) -> Subscriber:
        subscriber = Subscriber.create(
            IdentityDocumentFactory.create(),
            created_at=FIXED_CREATED_AT,
        )
        if with_account:
            subscriber.add_account(
                subscriber_code=SubscriberCodeFactory.create(),
                service_address_id=ServiceAddressId("address-001"),
                created_at=FIXED_CREATED_AT,
            )
        subscriber.pull_domain_events()
        return subscriber
