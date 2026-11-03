from __future__ import annotations

from collections.abc import Iterable

from customer_management.application.exceptions import ExternalServiceUnavailableError
from customer_management.application.ports.address_verification import (
    AddressVerificationPort,
)
from customer_management.domain.subscriber.service_address_id import ServiceAddressId


class MockAddressVerificationAdapter(AddressVerificationPort):
    OUTAGE_SERVICE_ADDRESS_ID = "ADDRESS-SERVICE-UNAVAILABLE"
    DEFAULT_SERVICEABLE_ADDRESS_IDS = frozenset(
        {
            "SERVICE-ADDRESS-001",
            "SERVICE-ADDRESS-002",
            "SERVICE-ADDRESS-003",
        }
    )

    def __init__(self, serviceable_address_ids: Iterable[str] | None = None) -> None:
        if serviceable_address_ids is None:
            self._serviceable_address_ids = self.DEFAULT_SERVICEABLE_ADDRESS_IDS
        else:
            self._serviceable_address_ids = frozenset(serviceable_address_ids)

    def is_serviceable(self, service_address_id: ServiceAddressId) -> bool:
        # Simulate a synchronous GIS BC call and translate its response into the
        # Customer Management port's serviceability decision (ACL boundary).
        gis_response = self._request_gis(service_address_id)
        return (
            gis_response["address_found"]
            and gis_response["within_service_area"]
        )

    def _request_gis(self, service_address_id: ServiceAddressId) -> dict[str, bool]:
        if service_address_id.value == self.OUTAGE_SERVICE_ADDRESS_ID:
            raise ExternalServiceUnavailableError("Address")

        is_known_serviceable_address = (
            service_address_id.value in self._serviceable_address_ids
        )
        return {
            "address_found": is_known_serviceable_address,
            "within_service_area": is_known_serviceable_address,
        }

