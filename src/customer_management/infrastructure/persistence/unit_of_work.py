from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.infrastructure.persistence.subscriber_repository import (
    SqlAlchemySubscriberRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._subscribers: SqlAlchemySubscriberRepository | None = None

    @property
    def subscribers(self) -> SqlAlchemySubscriberRepository:
        if self._subscribers is None:
            raise RuntimeError("Unit of Work has not been entered.")
        return self._subscribers

    def __enter__(self) -> Self:
        if self._session is not None:
            raise RuntimeError("Unit of Work is already active.")
        self._session = self._session_factory()
        self._subscribers = SqlAlchemySubscriberRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            self.rollback()
        finally:
            self._session.close()
            self._session = None
            self._subscribers = None

    def commit(self) -> None:
        session = self._require_session()
        repository = self.subscribers
        session.commit()
        for subscriber in repository.seen:
            subscriber.pull_domain_events()

    def rollback(self) -> None:
        self._require_session().rollback()

    def _require_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of Work has not been entered.")
        return self._session

