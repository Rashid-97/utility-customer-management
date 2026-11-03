from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


@dataclass(frozen=True, slots=True)
class CreateSubscriberAccountCommand:
    subscriber_id: Id[Subscriber]
    service_address_id: str
    city_code: str
    street_code: str
    building_code: str
    apartment_code: str
    application_date: date = field(default_factory=date.today)


@dataclass(frozen=True, slots=True)
class CreateSubscriberAccountResult:
    account_id: Id[SubscriberAccount]
    subscriber_code: str
    service_address_id: str
    status: str

