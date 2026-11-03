from __future__ import annotations

from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.exceptions import OutstandingDebtError
from customer_management.application.ports.address_verification import (
    AddressVerificationPort,
)
from customer_management.application.ports.identity_verification import (
    IdentityVerificationPort,
)
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.register_subscriber.command import (
    RegisteredSubscriberAccountResult,
    RegisterSubscriberCommand,
    RegisterSubscriberResult,
)
from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    IdentityVerificationRejectedError,
)
from customer_management.domain.subscriber.apartment_code import ApartmentCode
from customer_management.domain.subscriber.policies.application_verification import (
    ApplicationVerificationPolicy,
)
from customer_management.domain.subscriber.building_code import BuildingCode
from customer_management.domain.subscriber.city_code import CityCode
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.street_code import StreetCode
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_code import SubscriberCode


class RegisterSubscriberHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        identity_verification: IdentityVerificationPort,
        address_verification: AddressVerificationPort,
        outstanding_debt: OutstandingDebtPort,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._identity_verification = identity_verification
        self._address_verification = address_verification
        self._outstanding_debt = outstanding_debt

    def handle(self, command: RegisterSubscriberCommand) -> RegisterSubscriberResult:
        identity_document = self._identity_verification.verify_identity(
            command.document_type,
            command.document_number,
        )
        if identity_document is None:
            raise IdentityVerificationRejectedError()

        service_address_id = ServiceAddressId(command.service_address_id)
        subscriber_code = SubscriberCode.create(
            CityCode(command.city_code),
            StreetCode(command.street_code),
            BuildingCode(command.building_code),
            ApartmentCode(command.apartment_code),
        )

        with self._unit_of_work as unit_of_work:
            subscriber = unit_of_work.subscribers.find_by_identity_document(
                identity_document.document_type,
                identity_document.document_number,
            )
            is_new_subscriber = subscriber is None

            address_verified = self._address_verification.is_serviceable(
                service_address_id
            )
            ApplicationVerificationPolicy.verify(
                identity_verified=True,
                address_verified=address_verified,
                date_of_birth=identity_document.date_of_birth,
                application_date=command.application_date,
            )

            if unit_of_work.subscribers.exists_active_account_by_service_address(
                service_address_id
            ):
                raise ActiveAccountAlreadyExistsError(service_address_id.value)

            if subscriber is None:
                subscriber = Subscriber.create(identity_document)
            else:
                debt_account_ids = tuple(
                    account.id
                    for account in subscriber.accounts
                    if self._outstanding_debt.has_outstanding_debt(account.id)
                )
                if debt_account_ids:
                    raise OutstandingDebtError(debt_account_ids)

            subscriber.add_account(
                subscriber_code=subscriber_code,
                service_address_id=service_address_id,
            )
            unit_of_work.subscribers.save(subscriber)
            unit_of_work.commit()

        return RegisterSubscriberResult(
            subscriber_id=subscriber.id,
            first_name=subscriber.first_name,
            last_name=subscriber.last_name,
            date_of_birth=subscriber.date_of_birth,
            citizenship=subscriber.citizenship,
            accounts=tuple(
                RegisteredSubscriberAccountResult(
                    account_id=account.id,
                    subscriber_code=account.subscriber_code.value,
                    service_address_id=account.service_address_id.value,
                    status=account.status.value,
                )
                for account in subscriber.accounts
            ),
            is_new_subscriber=is_new_subscriber,
        )
