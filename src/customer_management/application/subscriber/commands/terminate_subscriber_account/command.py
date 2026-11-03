from __future__ import annotations

from dataclasses import dataclass

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


@dataclass(frozen=True, slots=True)
class TerminateSubscriberAccountCommand:
    subscriber_id: Id[Subscriber]
    account_id: Id[SubscriberAccount]

