from __future__ import annotations

from abc import ABC, abstractmethod

from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


class OutstandingDebtPort(ABC):
    @abstractmethod
    def has_outstanding_debt(self, account_id: Id[SubscriberAccount]) -> bool:
        raise NotImplementedError

