from datetime import UTC, datetime

import pytest

from customer_management.common.exceptions import InvalidDomainValueError
from customer_management.common.id import Id
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import (
    SubscriberAccount,
    SubscriberAccountStatus,
)
from tests.unit.factories.constants import FIXED_CREATED_AT
from tests.unit.factories.subscriber_code_factory import SubscriberCodeFactory


class TestSubscriberAccount:
    def test__reconstitute__when_active_state_is_valid__should_restore_account(self):
        # Arrange
        account_id = Id[SubscriberAccount].new()
        subscriber_id = Id[Subscriber].new()
        subscriber_code = SubscriberCodeFactory.create()
        service_address_id = ServiceAddressId("address-001")

        # Act
        result = SubscriberAccount.reconstitute(
            account_id=account_id,
            subscriber_id=subscriber_id,
            subscriber_code=subscriber_code,
            service_address_id=service_address_id,
            status=SubscriberAccountStatus.ACTIVE,
            created_at=FIXED_CREATED_AT,
            terminated_at=None,
        )

        # Assert
        assert result.id == account_id
        assert result.subscriber_id == subscriber_id
        assert result.subscriber_code == subscriber_code
        assert result.service_address_id == service_address_id
        assert result.status is SubscriberAccountStatus.ACTIVE
        assert result.is_active is True
        assert result.created_at == FIXED_CREATED_AT
        assert result.terminated_at is None

    def test__reconstitute__when_terminated_state_is_valid__should_restore_account(self):
        # Arrange
        terminated_at = datetime(2025, 6, 2, tzinfo=UTC)

        # Act
        result = SubscriberAccount.reconstitute(
            account_id=Id[SubscriberAccount].new(),
            subscriber_id=Id[Subscriber].new(),
            subscriber_code=SubscriberCodeFactory.create(),
            service_address_id=ServiceAddressId("address-001"),
            status=SubscriberAccountStatus.TERMINATED,
            created_at=FIXED_CREATED_AT,
            terminated_at=terminated_at,
        )

        # Assert
        assert result.status is SubscriberAccountStatus.TERMINATED
        assert result.is_active is False
        assert result.terminated_at == terminated_at

    def test__reconstitute__when_status_is_invalid__should_reject_state(self):
        # Arrange
        invalid_status = "ACTIVE"

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            SubscriberAccount.reconstitute(
                account_id=Id[SubscriberAccount].new(),
                subscriber_id=Id[Subscriber].new(),
                subscriber_code=SubscriberCodeFactory.create(),
                service_address_id=ServiceAddressId("address-001"),
                status=invalid_status,  # type: ignore[arg-type]
                created_at=FIXED_CREATED_AT,
                terminated_at=None,
            )

        # Assert
        assert str(exc_info.value) == "Subscriber account status is invalid."

    def test__reconstitute__when_active_account_has_termination_time__should_reject_state(
        self,
    ):
        # Arrange
        terminated_at = datetime(2025, 6, 2, tzinfo=UTC)

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            SubscriberAccount.reconstitute(
                account_id=Id[SubscriberAccount].new(),
                subscriber_id=Id[Subscriber].new(),
                subscriber_code=SubscriberCodeFactory.create(),
                service_address_id=ServiceAddressId("address-001"),
                status=SubscriberAccountStatus.ACTIVE,
                created_at=FIXED_CREATED_AT,
                terminated_at=terminated_at,
            )

        # Assert
        assert "active subscriber account" in str(exc_info.value)

    def test__reconstitute__when_terminated_account_lacks_termination_time__should_reject_state(
        self,
    ):
        # Arrange
        pass

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            SubscriberAccount.reconstitute(
                account_id=Id[SubscriberAccount].new(),
                subscriber_id=Id[Subscriber].new(),
                subscriber_code=SubscriberCodeFactory.create(),
                service_address_id=ServiceAddressId("address-001"),
                status=SubscriberAccountStatus.TERMINATED,
                created_at=FIXED_CREATED_AT,
                terminated_at=None,
            )

        # Assert
        assert "must have a termination time" in str(exc_info.value)
