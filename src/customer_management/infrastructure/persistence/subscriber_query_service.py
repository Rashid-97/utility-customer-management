from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from customer_management.application.ports.subscriber_query import (
    SubscriberAccountReadModel,
    SubscriberQueryPort,
    SubscriberReadModel,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount
from customer_management.infrastructure.persistence.models import (
    SubscriberAccountModel,
    SubscriberModel,
)


class SqlAlchemySubscriberQueryService(SubscriberQueryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_subscriber(
        self,
        subscriber_id: Id[Subscriber],
    ) -> SubscriberReadModel | None:
        subscriber_statement = select(
            SubscriberModel.id.label("subscriber_id"),
            SubscriberModel.first_name,
            SubscriberModel.last_name,
            SubscriberModel.date_of_birth,
            SubscriberModel.citizenship,
        ).where(SubscriberModel.id == subscriber_id.value)
        subscriber_row = self._session.execute(subscriber_statement).one_or_none()
        if subscriber_row is None:
            return None
        (
            subscriber_uuid,
            first_name,
            last_name,
            date_of_birth,
            citizenship,
        ) = subscriber_row

        accounts_statement = (
            select(
                SubscriberAccountModel.id.label("account_id"),
                SubscriberAccountModel.subscriber_code,
                SubscriberAccountModel.service_address_id,
                SubscriberAccountModel.status,
            )
            .where(SubscriberAccountModel.subscriber_id == subscriber_id.value)
            .order_by(
                SubscriberAccountModel.created_at,
                SubscriberAccountModel.id,
            )
        )
        account_rows = self._session.execute(accounts_statement).all()
        return SubscriberReadModel(
            subscriber_id=Id[Subscriber].from_uuid(subscriber_uuid),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            citizenship=citizenship,
            accounts=tuple(
                _account_projection(
                    account_uuid,
                    subscriber_code,
                    service_address_id,
                    account_status,
                )
                for (
                    account_uuid,
                    subscriber_code,
                    service_address_id,
                    account_status,
                ) in account_rows
            ),
        )

    def get_subscriber_account(
        self,
        subscriber_id: Id[Subscriber],
        account_id: Id[SubscriberAccount],
    ) -> SubscriberAccountReadModel | None:
        statement = select(
            SubscriberAccountModel.id.label("account_id"),
            SubscriberAccountModel.subscriber_code,
            SubscriberAccountModel.service_address_id,
            SubscriberAccountModel.status,
        ).where(
            SubscriberAccountModel.subscriber_id == subscriber_id.value,
            SubscriberAccountModel.id == account_id.value,
        )
        account_row = self._session.execute(statement).one_or_none()
        if account_row is None:
            return None
        account_uuid, subscriber_code, service_address_id, account_status = account_row
        return _account_projection(
            account_uuid,
            subscriber_code,
            service_address_id,
            account_status,
        )


def _account_projection(
    account_id: UUID,
    subscriber_code: str,
    service_address_id: str,
    status: str,
) -> SubscriberAccountReadModel:
    return SubscriberAccountReadModel(
        account_id=Id[SubscriberAccount].from_uuid(account_id),
        subscriber_code=subscriber_code,
        service_address_id=service_address_id,
        status=status,
    )

