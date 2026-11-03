from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from customer_management.common.id import Id


TAggregate = TypeVar("TAggregate")


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent(Generic[TAggregate]):
    """Immutable metadata shared by every domain event."""

    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: Id[TAggregate]
