from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from customer_management.common.exceptions import InvalidDomainValueError
from customer_management.domain.subscriber.apartment_code import ApartmentCode
from customer_management.domain.subscriber.building_code import BuildingCode
from customer_management.domain.subscriber.city_code import CityCode
from customer_management.domain.subscriber.identity_document import (
    DocumentType,
    IdentityDocument,
)
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.street_code import StreetCode
from customer_management.domain.subscriber.subscriber_code import SubscriberCode


class TestTextValueObjects:
    @pytest.mark.parametrize(
        ("value_type", "raw_value", "expected"),
        [
            (CityCode, " BAK ", "BAK"),
            (StreetCode, " NIZ ", "NIZ"),
            (BuildingCode, " 12 ", "12"),
            (ApartmentCode, " 34 ", "34"),
            (ServiceAddressId, " address-001 ", "address-001"),
            (SubscriberCode, " BAKNIZ1234 ", "BAKNIZ1234"),
        ],
        ids=["city", "street", "building", "apartment", "address", "subscriber-code"],
    )
    def test__init__when_text_has_surrounding_whitespace__should_normalize_value(
        self, value_type, raw_value, expected
    ):
        # Arrange
        pass

        # Act
        result = value_type(raw_value)

        # Assert
        assert result.value == expected
        assert str(result) == expected

    @pytest.mark.parametrize(
        "value_type",
        [CityCode, StreetCode, BuildingCode, ApartmentCode, ServiceAddressId, SubscriberCode],
        ids=["city", "street", "building", "apartment", "address", "subscriber-code"],
    )
    @pytest.mark.parametrize("raw_value", ["", "   "], ids=["empty", "whitespace"])
    def test__init__when_text_is_blank__should_reject_value(
        self, value_type, raw_value
    ):
        # Arrange
        pass

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            value_type(raw_value)

        # Assert
        assert exc_info.value is not None

    @pytest.mark.parametrize(
        "value_type",
        [CityCode, StreetCode, BuildingCode, ApartmentCode, ServiceAddressId, SubscriberCode],
        ids=["city", "street", "building", "apartment", "address", "subscriber-code"],
    )
    def test__init__when_value_is_not_text__should_reject_value(self, value_type):
        # Arrange
        invalid_value = 123

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            value_type(invalid_value)

        # Assert
        assert exc_info.value is not None

    def test__init__when_value_object_is_created__should_be_immutable(self):
        # Arrange
        sut = ServiceAddressId("address-001")

        # Act
        with pytest.raises(FrozenInstanceError) as exc_info:
            sut.value = "address-002"  # type: ignore[misc]

        # Assert
        assert exc_info.value is not None


class TestSubscriberCode:
    def test__create__when_components_are_valid__should_concatenate_in_domain_order(self):
        # Arrange
        city = CityCode("BAK")
        street = StreetCode("NIZ")
        building = BuildingCode("12")
        apartment = ApartmentCode("34")

        # Act
        result = SubscriberCode.create(city, street, building, apartment)

        # Assert
        assert result.value == "BAKNIZ1234"

    def test__create__when_component_type_is_wrong__should_reject_components(self):
        # Arrange
        city = CityCode("BAK")
        street = StreetCode("NIZ")
        building = BuildingCode("12")
        wrong_apartment = BuildingCode("34")

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            SubscriberCode.create(
                city, street, building, wrong_apartment  # type: ignore[arg-type]
            )

        # Assert
        assert "requires typed" in str(exc_info.value)


class TestIdentityDocument:
    def test__init__when_identity_fields_are_valid__should_normalize_text_fields(self):
        # Arrange
        date_of_birth = date(1990, 5, 20)

        # Act
        result = IdentityDocument(
            document_number=" AA1234567 ",
            document_type=DocumentType.NATIONAL_ID,
            first_name=" Ayla ",
            last_name=" Mammadova ",
            date_of_birth=date_of_birth,
            citizenship=" AZ ",
        )

        # Assert
        assert result.document_number == "AA1234567"
        assert result.first_name == "Ayla"
        assert result.last_name == "Mammadova"
        assert result.citizenship == "AZ"
        assert result.date_of_birth == date_of_birth

    @pytest.mark.parametrize(
        "field_name",
        ["document_number", "first_name", "last_name", "citizenship"],
    )
    @pytest.mark.parametrize(
        "invalid_value", ["", "   ", None], ids=["empty", "whitespace", "non-text"]
    )
    def test__init__when_identity_text_field_is_invalid__should_reject_value(
        self, field_name, invalid_value
    ):
        # Arrange
        values = {
            "document_number": "AA1234567",
            "document_type": DocumentType.NATIONAL_ID,
            "first_name": "Ayla",
            "last_name": "Mammadova",
            "date_of_birth": date(1990, 5, 20),
            "citizenship": "AZ",
        }
        values[field_name] = invalid_value

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            IdentityDocument(**values)

        # Assert
        assert exc_info.value is not None

    def test__init__when_document_type_is_invalid__should_reject_value(self):
        # Arrange
        invalid_document_type = "NATIONAL_ID"

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            IdentityDocument(
                document_number="AA1234567",
                document_type=invalid_document_type,  # type: ignore[arg-type]
                first_name="Ayla",
                last_name="Mammadova",
                date_of_birth=date(1990, 5, 20),
                citizenship="AZ",
            )

        # Assert
        assert str(exc_info.value) == "Document type is invalid."

    def test__init__when_date_of_birth_is_invalid__should_reject_value(self):
        # Arrange
        invalid_date_of_birth = "1990-05-20"

        # Act
        with pytest.raises(InvalidDomainValueError) as exc_info:
            IdentityDocument(
                document_number="AA1234567",
                document_type=DocumentType.NATIONAL_ID,
                first_name="Ayla",
                last_name="Mammadova",
                date_of_birth=invalid_date_of_birth,  # type: ignore[arg-type]
                citizenship="AZ",
            )

        # Assert
        assert str(exc_info.value) == "Date of birth is invalid."
