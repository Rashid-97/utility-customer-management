from __future__ import annotations

from typing import Generic, TypeVar

from customer_management.common.id import Id


TEntity = TypeVar("TEntity")


class DomainError(Exception):
    """Base class for domain rule violations."""


class InvalidDomainValueError(DomainError, ValueError):
    """Raised when a domain value cannot be constructed."""


class ApplicationVerificationError(DomainError):
    """Base class for rejected application facts."""


class IdentityVerificationRejectedError(ApplicationVerificationError):
    def __init__(self) -> None:
        super().__init__("Identity verification was rejected.")


class AddressVerificationRejectedError(ApplicationVerificationError):
    def __init__(self) -> None:
        super().__init__("The service address is not valid and serviceable.")


class ApplicantUnderageError(ApplicationVerificationError):
    def __init__(self, minimum_age: int) -> None:
        self.minimum_age = minimum_age
        super().__init__(f"Applicant must be at least {minimum_age} years old.")


class ActiveAccountAlreadyExistsError(DomainError):
    def __init__(self, service_address_id: str) -> None:
        self.service_address_id = service_address_id
        super().__init__(
            f"An active account already exists for service address "
            f"'{service_address_id}'."
        )


class SubscriberCodeAlreadyExistsError(DomainError):
    def __init__(self, subscriber_code: str) -> None:
        self.subscriber_code = subscriber_code
        super().__init__(f"Subscriber code '{subscriber_code}' is already in use.")


class SubscriberAccountNotFoundError(DomainError, Generic[TEntity]):
    def __init__(self, account_id: Id[TEntity]) -> None:
        self.account_id = account_id
        super().__init__(f"Subscriber account '{account_id}' was not found.")


class SubscriberAccountAlreadyTerminatedError(DomainError, Generic[TEntity]):
    def __init__(self, account_id: Id[TEntity]) -> None:
        self.account_id = account_id
        super().__init__(f"Subscriber account '{account_id}' is already terminated.")

