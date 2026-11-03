from dataclasses import dataclass

from customer_management.common.exceptions import InvalidDomainValueError
from customer_management.domain.subscriber.apartment_code import ApartmentCode
from customer_management.domain.subscriber.building_code import BuildingCode
from customer_management.domain.subscriber.city_code import CityCode
from customer_management.domain.subscriber.street_code import StreetCode


@dataclass(frozen=True, slots=True)
class SubscriberCode:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidDomainValueError("Subscriber code must be text.")
        normalized = self.value.strip()
        if not normalized:
            raise InvalidDomainValueError("Subscriber code must not be empty.")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def create(
        cls,
        city_code: CityCode,
        street_code: StreetCode,
        building_code: BuildingCode,
        apartment_code: ApartmentCode,
    ) -> "SubscriberCode":
        components = (city_code, street_code, building_code, apartment_code)
        expected_types = (CityCode, StreetCode, BuildingCode, ApartmentCode)
        if not all(
            isinstance(component, expected_type)
            for component, expected_type in zip(components, expected_types, strict=True)
        ):
            raise InvalidDomainValueError(
                "Subscriber code requires typed city, street, building and apartment codes."
            )
        return cls(
            city_code.value
            + street_code.value
            + building_code.value
            + apartment_code.value
        )

    def __str__(self) -> str:
        return self.value

