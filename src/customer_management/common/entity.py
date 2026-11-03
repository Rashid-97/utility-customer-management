from __future__ import annotations

from typing import Generic, TypeVar

from customer_management.common.id import Id


TEntity = TypeVar("TEntity")


class Entity(Generic[TEntity]):
    """Base class for domain objects whose identity defines equality."""

    def __init__(self, entity_id: Id[TEntity]) -> None:
        self._id = entity_id

    @property
    def id(self) -> Id[TEntity]:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))

