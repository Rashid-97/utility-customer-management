from __future__ import annotations

from abc import ABC, abstractmethod

from customer_management.domain.subscriber.service_address_id import ServiceAddressId


class AddressVerificationPort(ABC):
    @abstractmethod
    def is_serviceable(self, service_address_id: ServiceAddressId) -> bool:
        raise NotImplementedError

