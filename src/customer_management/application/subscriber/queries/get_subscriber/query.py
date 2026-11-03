from dataclasses import dataclass

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber


@dataclass(frozen=True, slots=True)
class GetSubscriberQuery:
    subscriber_id: Id[Subscriber]

