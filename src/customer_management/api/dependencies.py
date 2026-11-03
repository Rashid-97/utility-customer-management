from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.ports.address_verification import (
    AddressVerificationPort,
)
from customer_management.application.ports.identity_verification import (
    IdentityVerificationPort,
)
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.ports.subscriber_query import SubscriberQueryPort
from customer_management.application.subscriber.commands.create_subscriber_account.handler import (
    CreateSubscriberAccountHandler,
)
from customer_management.application.subscriber.commands.register_subscriber.handler import (
    RegisterSubscriberHandler,
)
from customer_management.application.subscriber.commands.terminate_subscriber_account.handler import (
    TerminateSubscriberAccountHandler,
)
from customer_management.application.subscriber.queries.get_subscriber.handler import (
    GetSubscriberHandler,
)
from customer_management.application.subscriber.queries.get_subscriber_account.handler import (
    GetSubscriberAccountHandler,
)
from customer_management.infrastructure.integrations.mock_address import (
    MockAddressVerificationAdapter,
)
from customer_management.infrastructure.integrations.mock_billing import (
    MockOutstandingDebtAdapter,
)
from customer_management.infrastructure.integrations.mock_identity import (
    MockIdentityVerificationAdapter,
)
from customer_management.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
    database_url_from_environment,
)
from customer_management.infrastructure.persistence.subscriber_query_service import (
    SqlAlchemySubscriberQueryService,
)
from customer_management.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


@lru_cache
def get_engine() -> Engine:
    return create_database_engine(database_url_from_environment())


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def dispose_engine() -> None:
    get_session_factory.cache_clear()
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()


def get_unit_of_work(
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


def get_subscriber_query(
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> Iterator[SubscriberQueryPort]:
    session = session_factory()
    try:
        yield SqlAlchemySubscriberQueryService(session)
    finally:
        session.close()


@lru_cache
def get_identity_verification() -> IdentityVerificationPort:
    return MockIdentityVerificationAdapter()


@lru_cache
def get_address_verification() -> AddressVerificationPort:
    return MockAddressVerificationAdapter()


@lru_cache
def get_outstanding_debt() -> OutstandingDebtPort:
    return MockOutstandingDebtAdapter()


def get_register_subscriber_handler(
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    identity_verification: IdentityVerificationPort = Depends(
        get_identity_verification
    ),
    address_verification: AddressVerificationPort = Depends(get_address_verification),
    outstanding_debt: OutstandingDebtPort = Depends(get_outstanding_debt),
) -> RegisterSubscriberHandler:
    return RegisterSubscriberHandler(
        unit_of_work,
        identity_verification,
        address_verification,
        outstanding_debt,
    )


def get_create_subscriber_account_handler(
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    address_verification: AddressVerificationPort = Depends(get_address_verification),
    outstanding_debt: OutstandingDebtPort = Depends(get_outstanding_debt),
) -> CreateSubscriberAccountHandler:
    return CreateSubscriberAccountHandler(
        unit_of_work,
        address_verification,
        outstanding_debt,
    )


def get_terminate_subscriber_account_handler(
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    outstanding_debt: OutstandingDebtPort = Depends(get_outstanding_debt),
) -> TerminateSubscriberAccountHandler:
    return TerminateSubscriberAccountHandler(unit_of_work, outstanding_debt)


def get_subscriber_handler(
    subscriber_query: SubscriberQueryPort = Depends(get_subscriber_query),
) -> GetSubscriberHandler:
    return GetSubscriberHandler(subscriber_query)


def get_subscriber_account_handler(
    subscriber_query: SubscriberQueryPort = Depends(get_subscriber_query),
) -> GetSubscriberAccountHandler:
    return GetSubscriberAccountHandler(subscriber_query)

