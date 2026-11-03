from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from customer_management.common.domain_event import DomainEvent

if TYPE_CHECKING:
    from customer_management.domain.subscriber.subscriber import Subscriber


@dataclass(frozen=True, slots=True, kw_only=True)
class SubscriberCreated(DomainEvent["Subscriber"]):
    """A Subscriber aggregate was created."""

