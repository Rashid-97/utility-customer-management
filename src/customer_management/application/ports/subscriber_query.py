from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


@dataclass(frozen=True, slots=True)
class SubscriberAccountReadModel:
    account_id: Id[SubscriberAccount]
    subscriber_code: str
    service_address_id: str
    status: str


@dataclass(frozen=True, slots=True)
class SubscriberReadModel:
    subscriber_id: Id[Subscriber]
    first_name: str
    last_name: str
    date_of_birth: date
    citizenship: str
    accounts: tuple[SubscriberAccountReadModel, ...]


class SubscriberQueryPort(ABC):
    @abstractmethod
    def get_subscriber(
        self,
        subscriber_id: Id[Subscriber],
    ) -> SubscriberReadModel | None:
        raise NotImplementedError

    @abstractmethod
    def get_subscriber_account(
        self,
        subscriber_id: Id[Subscriber],
        account_id: Id[SubscriberAccount],
    ) -> SubscriberAccountReadModel | None:
        raise NotImplementedError

