from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from customer_management.common.entity import Entity
from customer_management.common.exceptions import (
    InvalidDomainValueError,
    SubscriberAccountAlreadyTerminatedError,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber_code import SubscriberCode

if TYPE_CHECKING:
    from customer_management.domain.subscriber.subscriber import Subscriber


class SubscriberAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"


class SubscriberAccount(Entity["SubscriberAccount"]):
    """A child entity whose lifecycle is controlled by Subscriber."""

    def __init__(
        self,
        *,
        account_id: Id[SubscriberAccount],
        subscriber_id: Id[Subscriber],
        subscriber_code: SubscriberCode,
        service_address_id: ServiceAddressId,
        status: SubscriberAccountStatus,
        created_at: datetime,
        terminated_at: datetime | None,
    ) -> None:
        super().__init__(account_id)
        self._subscriber_id = subscriber_id
        self._subscriber_code = subscriber_code
        self._service_address_id = service_address_id
        self._status = status
        self._created_at = created_at
        self._terminated_at = terminated_at

        if not isinstance(status, SubscriberAccountStatus):
            raise InvalidDomainValueError("Subscriber account status is invalid.")
        if status is SubscriberAccountStatus.ACTIVE and terminated_at is not None:
            raise InvalidDomainValueError(
                "An active subscriber account cannot have a termination time."
            )
        if status is SubscriberAccountStatus.TERMINATED and terminated_at is None:
            raise InvalidDomainValueError(
                "A terminated subscriber account must have a termination time."
            )

    @classmethod
    def _create(
        cls,
        *,
        subscriber_id: Id[Subscriber],
        subscriber_code: SubscriberCode,
        service_address_id: ServiceAddressId,
        created_at: datetime | None = None,
    ) -> "SubscriberAccount":
        return cls(
            account_id=Id[SubscriberAccount].new(),
            subscriber_id=subscriber_id,
            subscriber_code=subscriber_code,
            service_address_id=service_address_id,
            status=SubscriberAccountStatus.ACTIVE,
            created_at=created_at or datetime.now(UTC),
            terminated_at=None,
        )

    @classmethod
    def reconstitute(
        cls,
        *,
        account_id: Id[SubscriberAccount],
        subscriber_id: Id[Subscriber],
        subscriber_code: SubscriberCode,
        service_address_id: ServiceAddressId,
        status: SubscriberAccountStatus,
        created_at: datetime,
        terminated_at: datetime | None,
    ) -> "SubscriberAccount":
        return cls(
            account_id=account_id,
            subscriber_id=subscriber_id,
            subscriber_code=subscriber_code,
            service_address_id=service_address_id,
            status=status,
            created_at=created_at,
            terminated_at=terminated_at,
        )

    @property
    def subscriber_id(self) -> Id[Subscriber]:
        return self._subscriber_id

    @property
    def subscriber_code(self) -> SubscriberCode:
        return self._subscriber_code

    @property
    def service_address_id(self) -> ServiceAddressId:
        return self._service_address_id

    @property
    def status(self) -> SubscriberAccountStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def terminated_at(self) -> datetime | None:
        return self._terminated_at

    @property
    def is_active(self) -> bool:
        return self._status is SubscriberAccountStatus.ACTIVE

    def _terminate(self, terminated_at: datetime | None = None) -> datetime:
        if not self.is_active:
            raise SubscriberAccountAlreadyTerminatedError(self.id)

        effective_time = terminated_at or datetime.now(UTC)
        self._status = SubscriberAccountStatus.TERMINATED
        self._terminated_at = effective_time
        return effective_time

