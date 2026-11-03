from __future__ import annotations

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from customer_management.common.id import Id
from customer_management.domain.subscriber.identity_document import DocumentType
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import (
    SubscriberAccountStatus,
)
from customer_management.domain.subscriber.repositories.subscriber_repository import (
    SubscriberRepository,
)
from customer_management.infrastructure.persistence.mappers import (
    subscriber_model_to_domain,
    subscriber_to_model,
    update_subscriber_model,
)
from customer_management.infrastructure.persistence.models import (
    SubscriberAccountModel,
    SubscriberModel,
)


class SqlAlchemySubscriberRepository(SubscriberRepository):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._seen: set[Subscriber] = set()

    @property
    def seen(self) -> frozenset[Subscriber]:
        return frozenset(self._seen)

    def get_by_id(self, subscriber_id: Id[Subscriber]) -> Subscriber | None:
        statement = (
            select(SubscriberModel)
            .where(SubscriberModel.id == subscriber_id.value)
            .options(selectinload(SubscriberModel.accounts))
        )
        model = self._session.scalar(statement)
        return self._track(model)

    def find_by_identity_document(
        self,
        document_type: DocumentType,
        document_number: str,
    ) -> Subscriber | None:
        statement = (
            select(SubscriberModel)
            .where(
                SubscriberModel.document_type == document_type.value,
                SubscriberModel.document_number == document_number,
            )
            .options(selectinload(SubscriberModel.accounts))
        )
        model = self._session.scalar(statement)
        return self._track(model)

    def exists_active_account_by_service_address(
        self,
        service_address_id: ServiceAddressId,
    ) -> bool:
        statement = select(
            exists().where(
                SubscriberAccountModel.service_address_id == service_address_id.value,
                SubscriberAccountModel.status
                == SubscriberAccountStatus.ACTIVE.value,
            )
        )
        return bool(self._session.scalar(statement))

    def save(self, subscriber: Subscriber) -> None:
        model = self._session.get(SubscriberModel, subscriber.id.value)
        if model is None:
            self._session.add(subscriber_to_model(subscriber))
        else:
            update_subscriber_model(subscriber, model)
        self._seen.add(subscriber)

    def _track(self, model: SubscriberModel | None) -> Subscriber | None:
        if model is None:
            return None
        subscriber = subscriber_model_to_domain(model)
        self._seen.add(subscriber)
        return subscriber

