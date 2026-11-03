from __future__ import annotations

from collections.abc import Iterable

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


class ApplicationError(Exception):
    """Base class for application-level failures."""


class SubscriberNotFoundError(ApplicationError):
    def __init__(self, subscriber_id: Id[Subscriber]) -> None:
        self.subscriber_id = subscriber_id
        super().__init__(f"Subscriber '{subscriber_id}' was not found.")


class OutstandingDebtError(ApplicationError):
    def __init__(self, account_ids: Iterable[Id[SubscriberAccount]]) -> None:
        self.account_ids = tuple(account_ids)
        super().__init__("Outstanding debt prevents this account operation.")


class ExternalServiceUnavailableError(ApplicationError):
    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        super().__init__(f"{service_name} service is currently unavailable.")

