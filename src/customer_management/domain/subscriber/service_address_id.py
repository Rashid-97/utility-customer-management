from dataclasses import dataclass

from customer_management.common.exceptions import InvalidDomainValueError


@dataclass(frozen=True, slots=True)
class ServiceAddressId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidDomainValueError("Service address ID must be text.")
        normalized = self.value.strip()
        if not normalized:
            raise InvalidDomainValueError("Service address ID must not be empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
