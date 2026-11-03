from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from customer_management.api.dependencies import (
    get_create_subscriber_account_handler,
    get_subscriber_account_handler,
    get_terminate_subscriber_account_handler,
)
from customer_management.api.schemas.requests import CreateSubscriberAccountRequest
from customer_management.api.schemas.responses import SubscriberAccountResponse
from customer_management.application.subscriber.commands.create_subscriber_account.command import (
    CreateSubscriberAccountCommand,
)
from customer_management.application.subscriber.commands.create_subscriber_account.handler import (
    CreateSubscriberAccountHandler,
)
from customer_management.application.subscriber.commands.terminate_subscriber_account.command import (
    TerminateSubscriberAccountCommand,
)
from customer_management.application.subscriber.commands.terminate_subscriber_account.handler import (
    TerminateSubscriberAccountHandler,
)
from customer_management.application.subscriber.queries.get_subscriber_account.handler import (
    GetSubscriberAccountHandler,
)
from customer_management.application.subscriber.queries.get_subscriber_account.query import (
    GetSubscriberAccountQuery,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber
from customer_management.domain.subscriber.subscriber_account import SubscriberAccount


router = APIRouter(prefix="/subscribers", tags=["subscriber accounts"])


@router.post(
    "/{subscriber_id}/accounts",
    response_model=SubscriberAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscriber_account(
    subscriber_id: UUID,
    request: CreateSubscriberAccountRequest,
    handler: CreateSubscriberAccountHandler = Depends(
        get_create_subscriber_account_handler
    ),
) -> SubscriberAccountResponse:
    result = handler.handle(
        CreateSubscriberAccountCommand(
            subscriber_id=Id[Subscriber].from_uuid(subscriber_id),
            service_address_id=request.service_address_id,
            city_code=request.city_code,
            street_code=request.street_code,
            building_code=request.building_code,
            apartment_code=request.apartment_code,
            application_date=date.today(),
        )
    )
    return SubscriberAccountResponse(
        account_id=result.account_id.value,
        subscriber_code=result.subscriber_code,
        service_address_id=result.service_address_id,
        status=result.status,
    )


@router.get(
    "/{subscriber_id}/accounts/{account_id}",
    response_model=SubscriberAccountResponse,
)
def get_subscriber_account(
    subscriber_id: UUID,
    account_id: UUID,
    handler: GetSubscriberAccountHandler = Depends(get_subscriber_account_handler),
) -> SubscriberAccountResponse:
    result = handler.handle(
        GetSubscriberAccountQuery(
            subscriber_id=Id[Subscriber].from_uuid(subscriber_id),
            account_id=Id[SubscriberAccount].from_uuid(account_id),
        )
    )
    return SubscriberAccountResponse(
        account_id=result.account_id.value,
        subscriber_code=result.subscriber_code,
        service_address_id=result.service_address_id,
        status=result.status,
    )


@router.post(
    "/{subscriber_id}/accounts/{account_id}/termination",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def terminate_subscriber_account(
    subscriber_id: UUID,
    account_id: UUID,
    handler: TerminateSubscriberAccountHandler = Depends(
        get_terminate_subscriber_account_handler
    ),
) -> Response:
    handler.handle(
        TerminateSubscriberAccountCommand(
            subscriber_id=Id[Subscriber].from_uuid(subscriber_id),
            account_id=Id[SubscriberAccount].from_uuid(account_id),
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

