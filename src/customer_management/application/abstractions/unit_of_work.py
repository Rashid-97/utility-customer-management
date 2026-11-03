from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from customer_management.domain.subscriber.repositories.subscriber_repository import (
    SubscriberRepository,
)


class UnitOfWork(ABC):
    """Owns one transaction and its aggregate repositories."""

    @property
    @abstractmethod
    def subscribers(self) -> SubscriberRepository:
        raise NotImplementedError

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError

