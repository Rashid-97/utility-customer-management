from datetime import date
from unittest.mock import MagicMock, Mock

import pytest

from customer_management.application.exceptions import OutstandingDebtError, SubscriberNotFoundError
from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.ports.address_verification import AddressVerificationPort
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.create_subscriber_account.handler import (
    CreateSubscriberAccountHandler,
)
from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    AddressVerificationRejectedError,
    ApplicantUnderageError,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.repositories.subscriber_repository import (
    SubscriberRepository,
)
from tests.unit.factories.create_subscriber_account_command_factory import (
    CreateSubscriberAccountCommandFactory,
)
from tests.unit.factories.subscriber_factory import SubscriberFactory


class TestCreateSubscriberAccountHandler:
    def setup_method(self):
        self.unit_of_work = MagicMock(spec=UnitOfWork)
        self.unit_of_work.__enter__.return_value = self.unit_of_work
        self.unit_of_work.__exit__.return_value = None
        self.unit_of_work.subscribers = Mock(spec=SubscriberRepository)
        self.address_verification = Mock(spec=AddressVerificationPort)
        self.outstanding_debt = Mock(spec=OutstandingDebtPort)
        self.subscriber = SubscriberFactory.create(with_account=True)
        self.unit_of_work.subscribers.get_by_id.return_value = self.subscriber
        self.unit_of_work.subscribers.exists_active_account_by_service_address.return_value = False
        self.address_verification.is_serviceable.return_value = True
        self.outstanding_debt.has_outstanding_debt.return_value = False
        self.sut = CreateSubscriberAccountHandler(
            self.unit_of_work, self.address_verification, self.outstanding_debt
        )

    def test__handle__when_request_is_valid__should_add_and_persist_account(self):
        # Arrange
        command = CreateSubscriberAccountCommandFactory.create(self.subscriber.id)

        # Act
        result = self.sut.handle(command)

        # Assert
        assert result.account_id == self.subscriber.accounts[-1].id
        assert result.subscriber_code == "BAKNIZ1235"
        assert result.service_address_id == "address-002"
        assert result.status == "ACTIVE"
        self.unit_of_work.subscribers.save.assert_called_once_with(self.subscriber)
        self.unit_of_work.commit.assert_called_once_with()

    def test__handle__when_subscriber_is_missing__should_raise_not_found_without_verification(self):
        # Arrange
        missing_id = Id[Subscriber].new()
        self.unit_of_work.subscribers.get_by_id.return_value = None
        command = CreateSubscriberAccountCommandFactory.create(missing_id)

        # Act
        with pytest.raises(SubscriberNotFoundError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.subscriber_id == missing_id
        self.address_verification.is_serviceable.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_address_is_not_serviceable__should_reject_without_write(self):
        # Arrange
        self.address_verification.is_serviceable.return_value = False
        command = CreateSubscriberAccountCommandFactory.create(self.subscriber.id)

        # Act
        with pytest.raises(AddressVerificationRejectedError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value is not None
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_subscriber_is_underage_at_application_date__should_reject_without_write(
        self,
    ):
        # Arrange
        command = CreateSubscriberAccountCommandFactory.create(
            self.subscriber.id, application_date=date(2005, 5, 19)
        )

        # Act
        with pytest.raises(ApplicantUnderageError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.minimum_age == 18
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_address_has_active_account__should_reject_before_debt_check(self):
        # Arrange
        self.unit_of_work.subscribers.exists_active_account_by_service_address.return_value = True
        command = CreateSubscriberAccountCommandFactory.create(self.subscriber.id)

        # Act
        with pytest.raises(ActiveAccountAlreadyExistsError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.service_address_id == "address-002"
        self.outstanding_debt.has_outstanding_debt.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()

    def test__handle__when_existing_account_has_debt__should_reject_without_write(self):
        # Arrange
        debtor_id = self.subscriber.accounts[0].id
        self.outstanding_debt.has_outstanding_debt.return_value = True
        command = CreateSubscriberAccountCommandFactory.create(self.subscriber.id)

        # Act
        with pytest.raises(OutstandingDebtError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.account_ids == (debtor_id,)
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()
