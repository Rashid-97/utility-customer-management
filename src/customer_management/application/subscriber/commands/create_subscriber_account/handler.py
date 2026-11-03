from __future__ import annotations

from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.exceptions import (
    OutstandingDebtError,
    SubscriberNotFoundError,
)
from customer_management.application.ports.address_verification import (
    AddressVerificationPort,
)
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.create_subscriber_account.command import (
    CreateSubscriberAccountCommand,
    CreateSubscriberAccountResult,
)
from customer_management.common.exceptions import ActiveAccountAlreadyExistsError
from customer_management.domain.subscriber.apartment_code import ApartmentCode
from customer_management.domain.subscriber.policies.application_verification import (
    ApplicationVerificationPolicy,
)
from customer_management.domain.subscriber.building_code import BuildingCode
from customer_management.domain.subscriber.city_code import CityCode
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.street_code import StreetCode
from customer_management.domain.subscriber.subscriber_code import SubscriberCode


class CreateSubscriberAccountHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        address_verification: AddressVerificationPort,
        outstanding_debt: OutstandingDebtPort,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._address_verification = address_verification
        self._outstanding_debt = outstanding_debt

    def handle(
        self,
        command: CreateSubscriberAccountCommand,
    ) -> CreateSubscriberAccountResult:
        service_address_id = ServiceAddressId(command.service_address_id)
        subscriber_code = SubscriberCode.create(
            CityCode(command.city_code),
            StreetCode(command.street_code),
            BuildingCode(command.building_code),
            ApartmentCode(command.apartment_code),
        )

        with self._unit_of_work as unit_of_work:
            subscriber = unit_of_work.subscribers.get_by_id(command.subscriber_id)
            if subscriber is None:
                raise SubscriberNotFoundError(command.subscriber_id)

            address_verified = self._address_verification.is_serviceable(
                service_address_id
            )
            ApplicationVerificationPolicy.verify(
                identity_verified=True,
                address_verified=address_verified,
                date_of_birth=subscriber.date_of_birth,
                application_date=command.application_date,
            )

            if unit_of_work.subscribers.exists_active_account_by_service_address(
                service_address_id
            ):
                raise ActiveAccountAlreadyExistsError(service_address_id.value)

            debt_account_ids = tuple(
                account.id
                for account in subscriber.accounts
                if self._outstanding_debt.has_outstanding_debt(account.id)
            )
            if debt_account_ids:
                raise OutstandingDebtError(debt_account_ids)

            account = subscriber.add_account(
                subscriber_code=subscriber_code,
                service_address_id=service_address_id,
            )
            unit_of_work.subscribers.save(subscriber)
            unit_of_work.commit()

        return CreateSubscriberAccountResult(
            account_id=account.id,
            subscriber_code=account.subscriber_code.value,
            service_address_id=account.service_address_id.value,
            status=account.status.value,
        )

