from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime

from customer_management.common.aggregate_root import AggregateRoot
from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    InvalidDomainValueError,
    SubscriberAccountNotFoundError,
    SubscriberCodeAlreadyExistsError,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.identity_document import IdentityDocument
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount
from customer_management.domain.subscriber.events.subscriber_account_created import (
    SubscriberAccountCreated,
)
from customer_management.domain.subscriber.events.subscriber_account_terminated import (
    SubscriberAccountTerminated,
)
from customer_management.domain.subscriber.events.subscriber_created import (
    SubscriberCreated,
)
from customer_management.domain.subscriber.subscriber_code import SubscriberCode


class Subscriber(AggregateRoot["Subscriber"]):
    """The sole aggregate root in Customer Management."""

    def __init__(
        self,
        *,
        subscriber_id: Id[Subscriber],
        identity_document: IdentityDocument,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        citizenship: str,
        accounts: Iterable[SubscriberAccount],
        created_at: datetime,
    ) -> None:
        super().__init__(subscriber_id)
        self._identity_document = identity_document
        self._first_name = first_name
        self._last_name = last_name
        self._date_of_birth = date_of_birth
        self._citizenship = citizenship
        self._accounts = list(accounts)
        self._created_at = created_at

        if any(account.subscriber_id != self.id for account in self._accounts):
            raise InvalidDomainValueError(
                "Every account in a Subscriber aggregate must belong to that Subscriber."
            )

        active_addresses = [
            account.service_address_id
            for account in self._accounts
            if account.is_active
        ]
        if len(active_addresses) != len(set(active_addresses)):
            raise InvalidDomainValueError(
                "A Subscriber cannot have multiple active accounts at one address."
            )

        subscriber_codes = [account.subscriber_code for account in self._accounts]
        if len(subscriber_codes) != len(set(subscriber_codes)):
            raise InvalidDomainValueError(
                "A Subscriber cannot have duplicate subscriber codes."
            )

    @classmethod
    def create(
        cls,
        identity_document: IdentityDocument,
        *,
        created_at: datetime | None = None,
    ) -> "Subscriber":
        effective_time = created_at or datetime.now(UTC)
        subscriber = cls(
            subscriber_id=Id[Subscriber].new(),
            identity_document=identity_document,
            first_name=identity_document.first_name,
            last_name=identity_document.last_name,
            date_of_birth=identity_document.date_of_birth,
            citizenship=identity_document.citizenship,
            accounts=(),
            created_at=effective_time,
        )
        subscriber._record_event(
            SubscriberCreated(
                aggregate_id=subscriber.id,
                occurred_at=effective_time,
            )
        )
        return subscriber

    @classmethod
    def reconstitute(
        cls,
        *,
        subscriber_id: Id[Subscriber],
        identity_document: IdentityDocument,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        citizenship: str,
        accounts: Iterable[SubscriberAccount],
        created_at: datetime,
    ) -> "Subscriber":
        return cls(
            subscriber_id=subscriber_id,
            identity_document=identity_document,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            citizenship=citizenship,
            accounts=accounts,
            created_at=created_at,
        )

    @property
    def identity_document(self) -> IdentityDocument:
        return self._identity_document

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def date_of_birth(self) -> date:
        return self._date_of_birth

    @property
    def citizenship(self) -> str:
        return self._citizenship

    @property
    def accounts(self) -> tuple[SubscriberAccount, ...]:
        return tuple(self._accounts)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def add_account(
        self,
        *,
        subscriber_code: SubscriberCode,
        service_address_id: ServiceAddressId,
        created_at: datetime | None = None,
    ) -> SubscriberAccount:
        if any(
            account.is_active and account.service_address_id == service_address_id
            for account in self._accounts
        ):
            raise ActiveAccountAlreadyExistsError(service_address_id.value)

        if any(
            account.subscriber_code == subscriber_code for account in self._accounts
        ):
            raise SubscriberCodeAlreadyExistsError(subscriber_code.value)

        account = SubscriberAccount._create(
            subscriber_id=self.id,
            subscriber_code=subscriber_code,
            service_address_id=service_address_id,
            created_at=created_at,
        )
        self._accounts.append(account)
        self._record_event(
            SubscriberAccountCreated(
                aggregate_id=self.id,
                account_id=account.id,
                subscriber_code=subscriber_code,
                service_address_id=service_address_id,
                occurred_at=account.created_at,
            )
        )
        return account

    def get_account(
        self,
        account_id: Id[SubscriberAccount],
    ) -> SubscriberAccount | None:
        return next(
            (account for account in self._accounts if account.id == account_id),
            None,
        )

    def terminate_account(
        self,
        account_id: Id[SubscriberAccount],
        *,
        terminated_at: datetime | None = None,
    ) -> None:
        account = self.get_account(account_id)
        if account is None:
            raise SubscriberAccountNotFoundError(account_id)

        effective_time = account._terminate(terminated_at)
        self._record_event(
            SubscriberAccountTerminated(
                aggregate_id=self.id,
                account_id=account.id,
                occurred_at=effective_time,
            )
        )

