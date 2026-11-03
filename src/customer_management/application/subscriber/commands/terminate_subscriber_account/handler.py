from __future__ import annotations

from customer_management.application.abstractions.unit_of_work import UnitOfWork
from customer_management.application.exceptions import (
    OutstandingDebtError,
    SubscriberNotFoundError,
)
from customer_management.application.ports.outstanding_debt import OutstandingDebtPort
from customer_management.application.subscriber.commands.terminate_subscriber_account.command import (
    TerminateSubscriberAccountCommand,
)
from customer_management.common.exceptions import SubscriberAccountNotFoundError


class TerminateSubscriberAccountHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        outstanding_debt: OutstandingDebtPort,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._outstanding_debt = outstanding_debt

    def handle(self, command: TerminateSubscriberAccountCommand) -> None:
        with self._unit_of_work as unit_of_work:
            subscriber = unit_of_work.subscribers.get_by_id(command.subscriber_id)
            if subscriber is None:
                raise SubscriberNotFoundError(command.subscriber_id)

            account = subscriber.get_account(command.account_id)
            if account is None:
                raise SubscriberAccountNotFoundError(command.account_id)

            if self._outstanding_debt.has_outstanding_debt(account.id):
                raise OutstandingDebtError((account.id,))

            subscriber.terminate_account(account.id)
            unit_of_work.subscribers.save(subscriber)
            unit_of_work.commit()

