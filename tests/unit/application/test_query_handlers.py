from datetime import date
from unittest.mock import Mock

import pytest

from customer_management.application.exceptions import SubscriberNotFoundError
from customer_management.application.ports.subscriber_query import (
    SubscriberAccountReadModel,
    SubscriberQueryPort,
    SubscriberReadModel,
)
from customer_management.application.subscriber.queries.get_subscriber.handler import (
    GetSubscriberHandler,
)
from customer_management.application.subscriber.queries.get_subscriber.query import (
    GetSubscriberQuery,
)
from customer_management.application.subscriber.queries.get_subscriber_account.handler import (
    GetSubscriberAccountHandler,
)
from customer_management.application.subscriber.queries.get_subscriber_account.query import (
    GetSubscriberAccountQuery,
)
from customer_management.common.exceptions import SubscriberAccountNotFoundError
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


class TestGetSubscriberHandler:
    def setup_method(self):
        self.subscriber_query = Mock(spec=SubscriberQueryPort)
        self.sut = GetSubscriberHandler(self.subscriber_query)

    def test__handle__when_subscriber_exists__should_return_projection(self):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        expected = SubscriberReadModel(
            subscriber_id=subscriber_id,
            first_name="Ayla",
            last_name="Mammadova",
            date_of_birth=date(1990, 5, 20),
            citizenship="AZ",
            accounts=(),
        )
        self.subscriber_query.get_subscriber.return_value = expected
        query = GetSubscriberQuery(subscriber_id=subscriber_id)

        # Act
        result = self.sut.handle(query)

        # Assert
        assert result is expected
        self.subscriber_query.get_subscriber.assert_called_once_with(subscriber_id)

    def test__handle__when_subscriber_is_missing__should_raise_not_found(self):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        self.subscriber_query.get_subscriber.return_value = None
        query = GetSubscriberQuery(subscriber_id=subscriber_id)

        # Act
        with pytest.raises(SubscriberNotFoundError) as exc_info:
            self.sut.handle(query)

        # Assert
        assert exc_info.value.subscriber_id == subscriber_id


class TestGetSubscriberAccountHandler:
    def setup_method(self):
        self.subscriber_query = Mock(spec=SubscriberQueryPort)
        self.sut = GetSubscriberAccountHandler(self.subscriber_query)

    def test__handle__when_account_exists__should_return_projection(self):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        account_id = Id[SubscriberAccount].new()
        expected = SubscriberAccountReadModel(
            account_id=account_id,
            subscriber_code="BAKNIZ1234",
            service_address_id="address-001",
            status="ACTIVE",
        )
        self.subscriber_query.get_subscriber_account.return_value = expected
        query = GetSubscriberAccountQuery(
            subscriber_id=subscriber_id, account_id=account_id
        )

        # Act
        result = self.sut.handle(query)

        # Assert
        assert result is expected
        self.subscriber_query.get_subscriber_account.assert_called_once_with(
            subscriber_id, account_id
        )

    def test__handle__when_account_is_missing__should_raise_not_found(self):
        # Arrange
        subscriber_id = Id[Subscriber].new()
        account_id = Id[SubscriberAccount].new()
        self.subscriber_query.get_subscriber_account.return_value = None
        query = GetSubscriberAccountQuery(
            subscriber_id=subscriber_id, account_id=account_id
        )

        # Act
        with pytest.raises(SubscriberAccountNotFoundError) as exc_info:
            self.sut.handle(query)

        # Assert
        assert exc_info.value.account_id == account_id
