from __future__ import annotations

from customer_management.common.id import Id
from customer_management.domain.subscriber.identity_document import (
    DocumentType,
    IdentityDocument,
)
from customer_management.domain.subscriber.service_address_id import ServiceAddressId
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import (
    SubscriberAccount,
    SubscriberAccountStatus,
)
from customer_management.domain.subscriber.subscriber_code import SubscriberCode
from customer_management.infrastructure.persistence.models import (
    SubscriberAccountModel,
    SubscriberModel,
)


def subscriber_model_to_domain(model: SubscriberModel) -> Subscriber:
    accounts = tuple(_account_model_to_domain(account) for account in model.accounts)
    identity_document = IdentityDocument(
        document_number=model.document_number,
        document_type=DocumentType(model.document_type),
        first_name=model.first_name,
        last_name=model.last_name,
        date_of_birth=model.date_of_birth,
        citizenship=model.citizenship,
    )
    return Subscriber.reconstitute(
        subscriber_id=Id[Subscriber].from_uuid(model.id),
        identity_document=identity_document,
        first_name=model.first_name,
        last_name=model.last_name,
        date_of_birth=model.date_of_birth,
        citizenship=model.citizenship,
        accounts=accounts,
        created_at=model.created_at,
    )


def subscriber_to_model(subscriber: Subscriber) -> SubscriberModel:
    model = SubscriberModel(
        id=subscriber.id.value,
        document_number=subscriber.identity_document.document_number,
        document_type=subscriber.identity_document.document_type.value,
        first_name=subscriber.first_name,
        last_name=subscriber.last_name,
        date_of_birth=subscriber.date_of_birth,
        citizenship=subscriber.citizenship,
        created_at=subscriber.created_at,
    )
    model.accounts = [_account_to_model(account) for account in subscriber.accounts]
    return model


def update_subscriber_model(
    subscriber: Subscriber,
    model: SubscriberModel,
) -> None:
    model.document_number = subscriber.identity_document.document_number
    model.document_type = subscriber.identity_document.document_type.value
    model.first_name = subscriber.first_name
    model.last_name = subscriber.last_name
    model.date_of_birth = subscriber.date_of_birth
    model.citizenship = subscriber.citizenship
    model.created_at = subscriber.created_at

    account_models_by_id = {
        Id[SubscriberAccount].from_uuid(account.id): account
        for account in model.accounts
    }
    aggregate_account_ids = {account.id for account in subscriber.accounts}
    removed_account_ids = set(account_models_by_id) - aggregate_account_ids
    if removed_account_ids:
        raise ValueError("Subscriber accounts cannot be removed from the aggregate.")

    for account in subscriber.accounts:
        account_model = account_models_by_id.get(account.id)
        if account_model is None:
            model.accounts.append(_account_to_model(account))
        else:
            _update_account_model(account, account_model)


def _account_model_to_domain(model: SubscriberAccountModel) -> SubscriberAccount:
    return SubscriberAccount.reconstitute(
        account_id=Id[SubscriberAccount].from_uuid(model.id),
        subscriber_id=Id[Subscriber].from_uuid(model.subscriber_id),
        subscriber_code=SubscriberCode(model.subscriber_code),
        service_address_id=ServiceAddressId(model.service_address_id),
        status=SubscriberAccountStatus(model.status),
        created_at=model.created_at,
        terminated_at=model.terminated_at,
    )


def _account_to_model(account: SubscriberAccount) -> SubscriberAccountModel:
    return SubscriberAccountModel(
        id=account.id.value,
        subscriber_id=account.subscriber_id.value,
        subscriber_code=account.subscriber_code.value,
        service_address_id=account.service_address_id.value,
        status=account.status.value,
        created_at=account.created_at,
        terminated_at=account.terminated_at,
    )


def _update_account_model(
    account: SubscriberAccount,
    model: SubscriberAccountModel,
) -> None:
    model.subscriber_id = account.subscriber_id.value
    model.subscriber_code = account.subscriber_code.value
    model.service_address_id = account.service_address_id.value
    model.status = account.status.value
    model.created_at = account.created_at
    model.terminated_at = account.terminated_at

