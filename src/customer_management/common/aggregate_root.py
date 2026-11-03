from __future__ import annotations

from typing import TypeVar

from customer_management.common.domain_event import DomainEvent
from customer_management.common.entity import Entity
from customer_management.common.id import Id


TAggregate = TypeVar("TAggregate")


class AggregateRoot(Entity[TAggregate]):
    """An entity that owns a consistency boundary and records its events."""

    def __init__(self, entity_id: Id[TAggregate]) -> None:
        super().__init__(entity_id)
        self._domain_events: list[DomainEvent[TAggregate]] = []

    @property
    def domain_events(self) -> tuple[DomainEvent[TAggregate], ...]:
        return tuple(self._domain_events)

    def _record_event(self, event: DomainEvent[TAggregate]) -> None:
        self._domain_events.append(event)

    def pull_domain_events(self) -> tuple[DomainEvent[TAggregate], ...]:
        events = tuple(self._domain_events)
        self._domain_events.clear()
        return events
