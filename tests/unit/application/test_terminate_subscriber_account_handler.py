from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

from customer_management.application.exceptions import OutstandingDebtError, SubscriberNotFoundError
from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.terminate_subscriber_account.command import (
    TerminateSubscriberAccountCommand,
)
from customer_management.application.subscriber.commands.terminate_subscriber_account.handler import (
    TerminateSubscriberAccountHandler,
)
from customer_management.common.exceptions import (
    SubscriberAccountAlreadyTerminatedError,
    SubscriberAccountNotFoundError,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.repositories.subscriber_repository import (
    SubscriberRepository,
)
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount
from tests.unit.factories.subscriber_factory import SubscriberFactory


class TestTerminateSubscriberAccountHandler:
    def setup_method(self):
        self.unit_of_work = MagicMock(spec=UnitOfWork)
        self.unit_of_work.__enter__.return_value = self.unit_of_work
        self.unit_of_work.__exit__.return_value = None
        self.unit_of_work.subscribers = Mock(spec=SubscriberRepository)
        self.outstanding_debt = Mock(spec=OutstandingDebtPort)
        self.subscriber = SubscriberFactory.create(with_account=True)
        self.account = self.subscriber.accounts[0]
        self.unit_of_work.subscribers.get_by_id.return_value = self.subscriber
        self.outstanding_debt.has_outstanding_debt.return_value = False
        self.sut = TerminateSubscriberAccountHandler(
            self.unit_of_work, self.outstanding_debt
        )

    def test__handle__when_account_is_debt_free__should_terminate_and_persist_account(self):
        # Arrange
        command = TerminateSubscriberAccountCommand(
            subscriber_id=self.subscriber.id,
            account_id=self.account.id,
        )

        # Act
        result = self.sut.handle(command)

        # Assert
        assert result is None
        assert self.account.is_active is False
        assert self.account.terminated_at is not None
        self.outstanding_debt.has_outstanding_debt.assert_called_once_with(self.account.id)
        self.unit_of_work.subscribers.save.assert_called_once_with(self.subscriber)
        self.unit_of_work.commit.assert_called_once_with()

    def test__handle__when_subscriber_is_missing__should_raise_not_found_without_debt_check(self):
        # Arrange
        missing_subscriber_id = Id[Subscriber].new()
        self.unit_of_work.subscribers.get_by_id.return_value = None
        command = TerminateSubscriberAccountCommand(
            subscriber_id=missing_subscriber_id,
            account_id=Id[SubscriberAccount].new(),
        )

        # Act
        with pytest.raises(SubscriberNotFoundError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.subscriber_id == missing_subscriber_id
        self.outstanding_debt.has_outstanding_debt.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_account_is_missing__should_raise_not_found_without_debt_check(self):
        # Arrange
        missing_account_id = Id[SubscriberAccount].new()
        command = TerminateSubscriberAccountCommand(
            subscriber_id=self.subscriber.id,
            account_id=missing_account_id,
        )

        # Act
        with pytest.raises(SubscriberAccountNotFoundError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.account_id == missing_account_id
        self.outstanding_debt.has_outstanding_debt.assert_not_called()
        self.unit_of_work.subscribers.save.assert_not_called()

    def test__handle__when_account_has_debt__should_reject_without_termination_or_write(self):
        # Arrange
        self.outstanding_debt.has_outstanding_debt.return_value = True
        command = TerminateSubscriberAccountCommand(
            subscriber_id=self.subscriber.id,
            account_id=self.account.id,
        )

        # Act
        with pytest.raises(OutstandingDebtError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.account_ids == (self.account.id,)
        assert self.account.is_active is True
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()

    def test__handle__when_account_is_already_terminated__should_propagate_domain_error_without_write(
        self,
    ):
        # Arrange
        self.subscriber.terminate_account(
            self.account.id, terminated_at=datetime(2025, 6, 2, tzinfo=UTC)
        )
        self.subscriber.pull_domain_events()
        command = TerminateSubscriberAccountCommand(
            subscriber_id=self.subscriber.id,
            account_id=self.account.id,
        )

        # Act
        with pytest.raises(SubscriberAccountAlreadyTerminatedError) as exc_info:
            self.sut.handle(command)

        # Assert
        assert exc_info.value.account_id == self.account.id
        self.unit_of_work.subscribers.save.assert_not_called()
        self.unit_of_work.commit.assert_not_called()
