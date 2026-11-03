from datetime import UTC, datetime

from customer_management.common.id import Id
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import (
    SubscriberAccount,
    SubscriberAccountStatus,
)
from tests.unit.factories.constants import FIXED_CREATED_AT
from tests.unit.factories.subscriber_code_factory import SubscriberCodeFactory


class SubscriberAccountFactory:
    @staticmethod
    def create(
        *,
        subscriber_id: Id[Subscriber],
        address: str = "address-001",
        apartment: str = "34",
        status: SubscriberAccountStatus = SubscriberAccountStatus.ACTIVE,
    ) -> SubscriberAccount:
        terminated_at = (
            datetime(2025, 6, 2, tzinfo=UTC)
            if status is SubscriberAccountStatus.TERMINATED
            else None
        )
        return SubscriberAccount.reconstitute(
            account_id=Id[SubscriberAccount].new(),
            subscriber_id=subscriber_id,
            subscriber_code=SubscriberCodeFactory.create(apartment=apartment),
            service_address_id=ServiceAddressId(address),
            status=status,
            created_at=FIXED_CREATED_AT,
            terminated_at=terminated_at,
        )
