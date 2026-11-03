from datetime import UTC, datetime

import pytest

from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    InvalidDomainValueError,
    SubscriberAccountAlreadyTerminatedError,
    SubscriberAccountNotFoundError,
    SubscriberCodeAlreadyExistsError,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.events.subscriber_account_created import (
    SubscriberAccountCreated,
)
from customer_management.domain.subscriber.events.subscriber_account_terminated import (
    SubscriberAccountTerminated,
)
from customer_management.domain.subscriber.events.subscriber_created import SubscriberCreated
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import (
    SubscriberAccount,
    SubscriberAccountStatus,
)
from tests.unit.factories.constants import FIXED_CREATED_AT
from tests.unit.factories.identity_document_factory import IdentityDocumentFactory
from tests.unit.factories.subscriber_account_factory import SubscriberAccountFactory
from tests.unit.factories.subscriber_code_factory import SubscriberCodeFactory
from tests.unit.factories.subscriber_factory import SubscriberFactory


class TestSubscriber:
    def test__create__when_identity_is_valid__should_initialize_subscriber_and_record_event(
        self,
    ):
        # Arrange
        identity_document = IdentityDocumentFactory.create()

        # Act
        result = Subscriber.create(identity_document, created_at=FIXED_CREATED_AT)

        # Assert
        assert result.identity_document == identity_document
        assert result.first_name == identity_document.first_name
        assert result.last_name == identity_document.last_name
        assert result.date_of_birth == identity_document.date_of_birth
        assert result.citizenship == identity_document.citizenship
        assert result.accounts == ()
        assert result.created_at == FIXED_CREATED_AT
        assert len(result.domain_events) == 1
        event = result.domain_events[0]
        assert isinstance(event, SubscriberCreated)
        assert event.aggregate_id == result.id
        assert event.occurred_at == FIXED_CREATED_AT

    def test__pull_domain_events__when_events_exist__should_return_and_clear_events(self):
        # Arrange
        sut = Subscriber.create(
            IdentityDocumentFactory.create(), created_at=FIXED_CREATED_AT
        )

        # Act
        result = sut.pull_domain_events()

        # Assert
        assert len(result) == 1
        assert sut.domain_events == ()

    def test__reconstitute__when_state_is_valid__should_restore_without_recording_events(
        self,
    ):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        account = SubscriberAccountFactory.create(subscriber_id=subscriber_id)
        identity_document = IdentityDocumentFactory.create()

        # Act
        result = Subscriber.reconstitute(
            subscriber_id=subscriber_id,
            identity_document=identity_document,
            first_name="Current Ayla",
            last_name="Current Mammadova",
            date_of_birth=identity_document.date_of_birth,
            citizenship="AZ",
            accounts=(account,),
            created_at=FIXED_CREATED_AT,
        )

        # Assert
        assert result.first_name == "Current Ayla"
        assert result.last_name == "Current Mammadova"
        assert result.accounts == (account,)
        assert result.domain_events == ()

    def test__reconstitute__when_account_belongs_to_another_subscriber__should_reject_state(
        self,
    ):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        foreign_account = SubscriberAccountFactory.create(
            subscriber_id=Id[Subscriber].new()
        )
        identity_document = IdentityDocumentFactory.create()

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            Subscriber.reconstitute(
                subscriber_id=subscriber_id,
                identity_document=identity_document,
                first_name="Ayla",
                last_name="Mammadova",
                date_of_birth=identity_document.date_of_birth,
                citizenship="AZ",
                accounts=(foreign_account,),
                created_at=FIXED_CREATED_AT,
            )

        # Assert
        assert "must belong" in str(exc_info.value)

    def test__reconstitute__when_active_accounts_share_address__should_reject_state(
        self,
    ):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        first = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id, apartment="34"
        )
        second = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id, apartment="35"
        )
        identity_document = IdentityDocumentFactory.create()

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            Subscriber.reconstitute(
                subscriber_id=subscriber_id,
                identity_document=identity_document,
                first_name="Ayla",
                last_name="Mammadova",
                date_of_birth=identity_document.date_of_birth,
                citizenship="AZ",
                accounts=(first, second),
                created_at=FIXED_CREATED_AT,
            )

        # Assert
        assert "multiple active accounts" in str(exc_info.value)

    def test__reconstitute__when_terminated_and_active_accounts_share_address__should_accept_state(
        self,
    ):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        terminated = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id,
            apartment="34",
            status=SubscriberAccountStatus.TERMINATED,
        )
        active = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id, apartment="35"
        )
        identity_document = IdentityDocumentFactory.create()

        # Act
        result = Subscriber.reconstitute(
            subscriber_id=subscriber_id,
            identity_document=identity_document,
            first_name="Ayla",
            last_name="Mammadova",
            date_of_birth=identity_document.date_of_birth,
            citizenship="AZ",
            accounts=(terminated, active),
            created_at=FIXED_CREATED_AT,
        )

        # Assert
        assert result.accounts == (terminated, active)

    def test__reconstitute__when_accounts_share_subscriber_code__should_reject_state(
        self,
    ):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        first = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id, address="address-001"
        )
        second = SubscriberAccountFactory.create(
            subscriber_id=subscriber_id, address="address-002"
        )
        identity_document = IdentityDocumentFactory.create()

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            Subscriber.reconstitute(
                subscriber_id=subscriber_id,
                identity_document=identity_document,
                first_name="Ayla",
                last_name="Mammadova",
                date_of_birth=identity_document.date_of_birth,
                citizenship="AZ",
                accounts=(first, second),
                created_at=FIXED_CREATED_AT,
            )

        # Assert
        assert "duplicate subscriber codes" in str(exc_info.value)

    def test__add_account__when_values_are_unique__should_add_active_account_and_record_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create()
        subscriber_code = SubscriberCodeFactory.create()
        service_address_id = ServiceAddressId("address-001")

        # Act
        result = sut.add_account(
            subscriber_code=subscriber_code,
            service_address_id=service_address_id,
            created_at=FIXED_CREATED_AT,
        )

        # Assert
        assert sut.accounts == (result,)
        assert result.subscriber_id == sut.id
        assert result.status is SubscriberAccountStatus.ACTIVE
        assert result.created_at == FIXED_CREATED_AT
        assert len(sut.domain_events) == 1
        event = sut.domain_events[0]
        assert isinstance(event, SubscriberAccountCreated)
        assert event.aggregate_id == sut.id
        assert event.account_id == result.id
        assert event.subscriber_code == subscriber_code
        assert event.service_address_id == service_address_id

    def test__add_account__when_active_account_has_same_address__should_reject_without_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)

        # Act
        with pytest.raises(ActiveAccountAlreadyExistsError) as exc_info:
            sut.add_account(
                subscriber_code=SubscriberCodeFactory.create(apartment="35"),
                service_address_id=ServiceAddressId("address-001"),
            )

        # Assert
        assert exc_info.value.service_address_id == "address-001"
        assert len(sut.accounts) == 1
        assert sut.domain_events == ()

    def test__add_account__when_subscriber_code_already_exists__should_reject_without_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)

        # Act
        with pytest.raises(SubscriberCodeAlreadyExistsError) as exc_info:
            sut.add_account(
                subscriber_code=SubscriberCodeFactory.create(),
                service_address_id=ServiceAddressId("address-002"),
            )

        # Assert
        assert exc_info.value.subscriber_code == "BAKNIZ1234"
        assert len(sut.accounts) == 1
        assert sut.domain_events == ()

    def test__get_account__when_account_exists__should_return_account(self):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)
        expected_account = sut.accounts[0]

        # Act
        result = sut.get_account(expected_account.id)

        # Assert
        assert result is expected_account

    def test__get_account__when_account_does_not_exist__should_return_none(self):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)
        missing_id = Id[SubscriberAccount].new()

        # Act
        result = sut.get_account(missing_id)

        # Assert
        assert result is None

    def test__terminate_account__when_account_is_active__should_terminate_and_record_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)
        account = sut.accounts[0]
        terminated_at = datetime(2025, 6, 2, 9, 0, tzinfo=UTC)

        # Act
        result = sut.terminate_account(account.id, terminated_at=terminated_at)

        # Assert
        assert result is None
        assert account.status is SubscriberAccountStatus.TERMINATED
        assert account.terminated_at == terminated_at
        assert len(sut.domain_events) == 1
        event = sut.domain_events[0]
        assert isinstance(event, SubscriberAccountTerminated)
        assert event.aggregate_id == sut.id
        assert event.account_id == account.id
        assert event.occurred_at == terminated_at

    def test__terminate_account__when_account_is_missing__should_raise_not_found_without_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)
        missing_id = Id[SubscriberAccount].new()

        # Act
        with pytest.raises(SubscriberAccountNotFoundError) as exc_info:
            sut.terminate_account(missing_id)

        # Assert
        assert exc_info.value.account_id == missing_id
        assert sut.domain_events == ()

    def test__terminate_account__when_account_is_already_terminated__should_reject_without_new_event(
        self,
    ):
        # Arrange
        sut = SubscriberFactory.create(with_account=True)
        account = sut.accounts[0]
        sut.terminate_account(account.id, terminated_at=datetime(2025, 6, 2, tzinfo=UTC))
        sut.pull_domain_events()

        # Act
        with pytest.raises(SubscriberAccountAlreadyTerminatedError) as exc_info:
            sut.terminate_account(
                account.id, terminated_at=datetime(2025, 6, 3, tzinfo=UTC)
            )

        # Assert
        assert exc_info.value.account_id == account.id
        assert account.terminated_at == datetime(2025, 6, 2, tzinfo=UTC)
        assert sut.domain_events == ()
