from customer_management.application.ports.subscriber_query import (
    SubscriberAccountReadModel,
    SubscriberQueryPort,
)
from customer_management.application.subscriber.queries.get_subscriber_account.query import (
    GetSubscriberAccountQuery,
)
from customer_management.common.exceptions import SubscriberAccountNotFoundError


class GetSubscriberAccountHandler:
    def __init__(self, subscriber_query: SubscriberQueryPort) -> None:
        self._subscriber_query = subscriber_query

    def handle(
        self,
        query: GetSubscriberAccountQuery,
    ) -> SubscriberAccountReadModel:
        account = self._subscriber_query.get_subscriber_account(
            query.subscriber_id,
            query.account_id,
        )
        if account is None:
            raise SubscriberAccountNotFoundError(query.account_id)
        return account

