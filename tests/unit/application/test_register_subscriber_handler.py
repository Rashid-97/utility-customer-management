from datetime import date
from unittest.mock import MagicMock, Mock

import pytest

from customer_management.application.exceptions import OutstandingDebtError
from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.ports.address_verification import AddressVerificationPort
from customer_management.application.ports.identity_verification import IdentityVerificationPort
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.register_subscriber.handler import (
    RegisterSubscriberHandler,
)
from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    AddressVerificationRejectedError,
    ApplicantUnderageError,
    IdentityVerificationRejectedError,
)
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.repositories.subscriber_repository import (
    SubscriberRepository,
)
from customer_management.domain.subscriber.subscriber_account import SubscriberAccountStatus
from tests.unit.factories.identity_document_factory import IdentityDocumentFactory
from tests.unit.factories.register_subscriber_command_factory import (
    RegisterSubscriberCommandFactory,
)
from tests.unit.factories.subscriber_code_factory import SubscriberCodeFactory
from tests.unit.factories.subscriber_factory import SubscriberFactory


class TestRegisterSubscriberHandler:
    def setup_method(self):
        self.unit_of_work = MagicMock(spec=UnitOfWork)
        self.unit_of_work.__enter__.return_value = self.unit_of_work
        self.unit_of_work.__exit__.return_value = None
        self.unit_of_work.subscribers = Mock(spec=SubscriberRepository)
        self.identity_verification = Mock(spec=IdentityVerificationPort)
        self.address_verification = Mock(spec=AddressVerificationPort)
        self.outstanding_debt = Mock(spec=OutstandingDebtPort)
        self.identity_document = IdentityDocumentFactory.create()
        self.identity_verification.verify_identity.return_value = self.identity_document
        self.address_verification.is_serviceable.return_value = True
        self.unit_of_work.subscribers.find_by_identity_document.return_value = None
        self.unit_of_work.subscribers.exists_active_account_by_service_address.return_value = False
        self.outstanding_debt.has_outstanding_debt.return_value = False
        self.sut = RegisterSubscriberHandler(
            self.unit_of_work,
            self.identity_verification,
            self.address_verification,
            self.outstanding_debt,
        )

    def test__handle__when_new_application_is_valid__should_create_subscriber_and_first_account(
        self,
    ):
        # Arrange
        command = RegisterSubscriberCommandFactory.create()

        # Act
        result = self.sut.handle(command)

        # Assert
        assert result.is_new_subscriber is True
        assert result.first_name == self.identity_document.first_name
        assert result.last_name == self.identity_document.last_name
        assert result.date_of_birth == self.identity_document.date_of_birth
        assert result.citizenship == self.identity_document.citizenship
        assert len(result.accounts) == 1
        assert result.accounts[0].subscriber_code == "BAKNIZ1235"
        assert result.accounts[0].service_address_id == "address-002"
        assert result.accounts[0].status == SubscriberAccountStatus.ACTIVE.value
        saved = self.unit_of_work.subscribers.save.call_args.args[0]
        assert saved.id == result.subscriber_id
        self.unit_of_work.commit.assert_called_once_with()
        self.outstanding_debt.has_outstanding_debt.assert_not_called()

    def test__handle__when_subscriber_exists_and_is_debt_free__should_add_account_without_duplicate_subscriber(
        self,
    ):
        # Arrange
        existing = SubscriberFactory.create(with_account=True)
        self.unit_of_work.subscribers.find_by_identity_document.return_value = existing
        command = RegisterSubscriberCommandFactory.create()

        # Act
        result = self.sut.handle(command)

        # Assert
        assert result.is_new_subscriber is False
        assert result.subscriber_id == existing.id
        assert len(result.accounts) == 2
        self.outstanding_debt.has_outstanding_debt.assert_called_once_with(existing.accounts[0].id)
        self.unit_of_work.subscribers.save.assert_called_once_with(existing)
        self.unit_of_work.commit.assert_called_once_with()

    def test__handle__when_identity_is_rejected__should_fail_before_transaction(self):
        # Arrange
        self.identity_verification.verify_identity.return_value = None
        command = RegisterSubscriberCommandFactory.create()

        # Act
        with pytest.raises(IdentityVerificationRejectedError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert str(exc_info.value) == "Identity verification was rejected."
        self.unit_of_work.__enter__.assert_not_called()
        self.address_verification.is_serviceable.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_address_is_not_serviceable__should_reject_without_write(self):
        # Arrange
        self.address_verification.is_serviceable.return_value = False
        command = RegisterSubscriberCommandFactory.create()

        # Act
        with pytest.raises(AddressVerificationRejectedError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value is not None
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_verified_applicant_is_underage__should_reject_without_write(self):
        # Arrange
        self.identity_verification.verify_identity.return_value = IdentityDocumentFactory.create(
            date_of_birth=date(2008, 6, 2)
        )
        command = RegisterSubscriberCommandFactory.create(
            application_date=date(2025, 6, 1)
        )

        # Act
        with pytest.raises(ApplicantUnderageError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.minimum_age == 18
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_address_has_active_account__should_reject_without_debt_check_or_write(
        self,
    ):
        # Arrange
        existing = SubscriberFactory.create(with_account=True)
        self.unit_of_work.subscribers.find_by_identity_document.return_value = existing
        self.unit_of_work.subscribers.exists_active_account_by_service_address.return_value = True
        command = RegisterSubscriberCommandFactory.create()

        # Act
        with pytest.raises(ActiveAccountAlreadyExistsError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.service_address_id == "address-002"
        self.outstanding_debt.has_outstanding_debt.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_existing_subscriber_has_debt__should_report_debtor_accounts_without_write(
        self,
    ):
        # Arrange
        existing = SubscriberFactory.create(with_account=True)
        existing.add_account(
            subscriber_code=SubscriberCodeFactory.create(apartment="36"),
            service_address_id=ServiceAddressId("address-003"),
        )
        existing.pull_domain_events()
        debtor_id = existing.accounts[1].id
        self.unit_of_work.subscribers.find_by_identity_document.return_value = existing
        self.outstanding_debt.has_outstanding_debt.side_effect = (
            lambda account_id: account_id == debtor_id
        )
        command = RegisterSubscriberCommandFactory.create()

        # Act
        with pytest.raises(OutstandingDebtError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.account_ids == (debtor_id,)
        assert self.outstanding_debt.has_outstanding_debt.call_count == 2
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()
