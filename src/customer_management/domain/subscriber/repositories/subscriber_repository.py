from __future__ import annotations

from abc import ABC, abstractmethod

from customer_management.common.id import Id
from customer_management.domain.subscriber.identity_document import DocumentType
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber


class SubscriberRepository(ABC):
    @abstractmethod
    def get_by_id(self, subscriber_id: Id[Subscriber]) -> Subscriber | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_identity_document(
        self,
        document_type: DocumentType,
        document_number: str,
    ) -> Subscriber | None:
        raise NotImplementedError

    @abstractmethod
    def exists_active_account_by_service_address(
        self,
        service_address_id: ServiceAddressId,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, subscriber: Subscriber) -> None:
        raise NotImplementedError

