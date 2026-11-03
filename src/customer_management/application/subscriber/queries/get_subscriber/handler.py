from customer_management.application.exceptions import SubscriberNotFoundError
from customer_management.application.ports.subscriber_query import (
    SubscriberQueryPort,
    SubscriberReadModel,
)
from customer_management.application.subscriber.queries.get_subscriber.query import (
    GetSubscriberQuery,
)


class GetSubscriberHandler:
    def __init__(self, subscriber_query: SubscriberQueryPort) -> None:
        self._subscriber_query = subscriber_query

    def handle(self, query: GetSubscriberQuery) -> SubscriberReadModel:
        subscriber = self._subscriber_query.get_subscriber(query.subscriber_id)
        if subscriber is None:
            raise SubscriberNotFoundError(query.subscriber_id)
        return subscriber

