from customer_management.domain.subscriber.apartment_code import ApartmentCode
from customer_management.domain.subscriber.building_code import BuildingCode
from customer_management.domain.subscriber.city_code import CityCode
from customer_management.domain.subscriber.street_code import StreetCode
from customer_management.domain.subscriber.subscriber_code import SubscriberCode


class SubscriberCodeFactory:
    @staticmethod
    def create(
        *,
        city: str = "BAK",
        street: str = "NIZ",
        building: str = "12",
        apartment: str = "34",
    ) -> SubscriberCode:
        return SubscriberCode.create(
            CityCode(city),
            StreetCode(street),
            BuildingCode(building),
            ApartmentCode(apartment),
        )
