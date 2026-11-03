from datetime import date

from customer_management.common.exceptions import (
    AddressVerificationRejectedError,
    ApplicantUnderageError,
    IdentityVerificationRejectedError,
)


class ApplicationVerificationPolicy:
    MINIMUM_AGE = 18

    @classmethod
    def verify(
        cls,
        *,
        identity_verified: bool,
        address_verified: bool,
        date_of_birth: date,
        application_date: date,
    ) -> None:
        if not identity_verified:
            raise IdentityVerificationRejectedError()
        if not address_verified:
            raise AddressVerificationRejectedError()

        age = application_date.year - date_of_birth.year
        if (application_date.month, application_date.day) < (
            date_of_birth.month,
            date_of_birth.day,
        ):
            age -= 1

        if age < cls.MINIMUM_AGE:
            raise ApplicantUnderageError(cls.MINIMUM_AGE)

