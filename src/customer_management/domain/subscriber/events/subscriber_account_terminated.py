from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from customer_management.common.domain_event import DomainEvent
from customer_management.common.id import Id

if TYPE_CHECKING:
    from customer_management.domain.subscriber.subscriber import Subscriber
    from customer_management.domain.subscriber.subscriber_account import (
        SubscriberAccount,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SubscriberAccountTerminated(DomainEvent["Subscriber"]):
    account_id: Id[SubscriberAccount]

