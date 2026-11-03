from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Self, TypeVar
from uuid import UUID, uuid4


TEntity = TypeVar("TEntity")


@dataclass(frozen=True, slots=True)
class Id(Generic[TEntity]):
    """An immutable UUID identity associated with one concrete entity type."""

    _value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self._value, UUID):
            raise TypeError("Id value must be a UUID.")

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())

    @classmethod
    def from_uuid(cls, value: UUID) -> Self:
        return cls(value)

    @property
    def value(self) -> UUID:
        return self._value

    def __str__(self) -> str:
        return str(self._value)
