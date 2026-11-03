from __future__ import annotations

from collections.abc import Iterable

from customer_management.application.exceptions import ExternalServiceUnavailableError
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


class MockOutstandingDebtAdapter(OutstandingDebtPort):
    def __init__(
        self,
        outstanding_account_ids: Iterable[Id[SubscriberAccount]] = (),
        *,
        unavailable: bool = False,
    ) -> None:
        self._outstanding_account_ids = frozenset(outstanding_account_ids)
        self._unavailable = unavailable

    def has_outstanding_debt(self, account_id: Id[SubscriberAccount]) -> bool:
        if self._unavailable:
            raise ExternalServiceUnavailableError("Billing")
        return account_id in self._outstanding_account_ids

