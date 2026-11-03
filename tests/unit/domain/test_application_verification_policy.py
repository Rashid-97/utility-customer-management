from datetime import date

import pytest

from customer_management.common.exceptions import (
    AddressVerificationRejectedError,
    ApplicantUnderageError,
    IdentityVerificationRejectedError,
)
from customer_management.domain.subscriber.policies.application_verification import (
    ApplicationVerificationPolicy,
)


class TestApplicationVerificationPolicy:
    def test__verify__when_all_facts_are_valid__should_accept_application(self):
        # Arrange
        date_of_birth = date(1990, 5, 20)
        application_date = date(2025, 6, 1)

        # Act
        result = ApplicationVerificationPolicy.verify(
            identity_verified=True,
            address_verified=True,
            date_of_birth=date_of_birth,
            application_date=application_date,
        )

        # Assert
        assert result is None

    def test__verify__when_identity_is_rejected__should_raise_identity_error_first(self):
        # Arrange
        date_of_birth = date(2010, 1, 1)
        application_date = date(2025, 1, 1)

        # Act
        with pytest.raises(IdentityVerificationRejectedError) as exc_info:
            ApplicationVerificationPolicy.verify(
                identity_verified=False,
                address_verified=False,
                date_of_birth=date_of_birth,
                application_date=application_date,
            )

        # Assert
        assert str(exc_info.value) == "Identity verification was rejected."

    def test__verify__when_address_is_rejected__should_raise_address_error(self):
        # Arrange
        date_of_birth = date(1990, 5, 20)
        application_date = date(2025, 6, 1)

        # Act
        with pytest.raises(AddressVerificationRejectedError) as exc_info:
            ApplicationVerificationPolicy.verify(
                identity_verified=True,
                address_verified=False,
                date_of_birth=date_of_birth,
                application_date=application_date,
            )

        # Assert
        assert "not valid and serviceable" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("date_of_birth", "application_date"),
        [
            (date(2007, 6, 2), date(2025, 6, 1)),
            (date(2007, 12, 31), date(2025, 1, 1)),
        ],
        ids=["birthday-tomorrow", "birthday-later-in-year"],
    )
    def test__verify__when_applicant_is_seventeen__should_raise_underage_error(
        self, date_of_birth, application_date
    ):
        # Arrange
        pass

        # Act
        with pytest.raises(ApplicantUnderageError) as exc_info:
            ApplicationVerificationPolicy.verify(
                identity_verified=True,
                address_verified=True,
                date_of_birth=date_of_birth,
                application_date=application_date,
            )

        # Assert
        assert exc_info.value.minimum_age == 18

    def test__verify__when_applicant_turns_eighteen_today__should_accept_application(self):
        # Arrange
        date_of_birth = date(2007, 6, 1)
        application_date = date(2025, 6, 1)

        # Act
        result = ApplicationVerificationPolicy.verify(
            identity_verified=True,
            address_verified=True,
            date_of_birth=date_of_birth,
            application_date=application_date,
        )

        # Assert
        assert result is None

    def test__verify__when_birthday_has_passed_in_eighteenth_year__should_accept_application(
        self,
    ):
        # Arrange
        date_of_birth = date(2007, 5, 31)
        application_date = date(2025, 6, 1)

        # Act
        result = ApplicationVerificationPolicy.verify(
            identity_verified=True,
            address_verified=True,
            date_of_birth=date_of_birth,
            application_date=application_date,
        )

        # Assert
        assert result is None
