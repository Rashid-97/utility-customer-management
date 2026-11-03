from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from customer_management.common.id import Id
from customer_management.domain.subscriber.identity_document import DocumentType
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


@dataclass(frozen=True, slots=True)
class RegisterSubscriberCommand:
    document_number: str
    document_type: DocumentType
    service_address_id: str
    city_code: str
    street_code: str
    building_code: str
    apartment_code: str
    application_date: date = field(default_factory=date.today)


@dataclass(frozen=True, slots=True)
class RegisteredSubscriberAccountResult:
    account_id: Id[SubscriberAccount]
    subscriber_code: str
    service_address_id: str
    status: str


@dataclass(frozen=True, slots=True)
class RegisterSubscriberResult:
    subscriber_id: Id[Subscriber]
    first_name: str
    last_name: str
    date_of_birth: date
    citizenship: str
    accounts: tuple[RegisteredSubscriberAccountResult, ...]
    is_new_subscriber: bool
