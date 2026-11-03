from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from customer_management.api.dependencies import (
    get_register_subscriber_handler,
    get_subscriber_handler,
)
from customer_management.api.schemas.requests import RegisterSubscriberRequest
from customer_management.api.schemas.responses import (
    SubscriberAccountResponse,
    SubscriberResponse,
)
from customer_management.application.ports.subscriber_query import SubscriberReadModel
from customer_management.application.subscriber.commands.register_subscriber.command import (
    RegisterSubscriberCommand,
    RegisterSubscriberResult,
)
from customer_management.application.subscriber.commands.register_subscriber.handler import (
    RegisterSubscriberHandler,
)
from customer_management.application.subscriber.queries.get_subscriber.handler import (
    GetSubscriberHandler,
)
from customer_management.application.subscriber.queries.get_subscriber.query import (
    GetSubscriberQuery,
)
from customer_management.common.id import Id
from customer_management.domain.subscriber.subscriber import Subscriber


router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.post(
    "",
    response_model=SubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_200_OK: {"model": SubscriberResponse}},
)
def register_subscriber(
    request: RegisterSubscriberRequest,
    response: Response,
    handler: RegisterSubscriberHandler = Depends(get_register_subscriber_handler),
) -> SubscriberResponse:
    result = handler.handle(
        RegisterSubscriberCommand(
            document_number=request.document_number,
            document_type=request.document_type,
            service_address_id=request.service_address_id,
            city_code=request.city_code,
            street_code=request.street_code,
            building_code=request.building_code,
            apartment_code=request.apartment_code,
            application_date=date.today(),
        )
    )
    if not result.is_new_subscriber:
        response.status_code = status.HTTP_200_OK
    return _registration_response(result)


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
def get_subscriber(
    subscriber_id: UUID,
    handler: GetSubscriberHandler = Depends(get_subscriber_handler),
) -> SubscriberResponse:
    result = handler.handle(
        GetSubscriberQuery(
            subscriber_id=Id[Subscriber].from_uuid(subscriber_id),
        )
    )
    return _subscriber_response(result)


def _registration_response(result: RegisterSubscriberResult) -> SubscriberResponse:
    return SubscriberResponse(
        subscriber_id=result.subscriber_id.value,
        first_name=result.first_name,
        last_name=result.last_name,
        date_of_birth=result.date_of_birth,
        citizenship=result.citizenship,
        accounts=[
            SubscriberAccountResponse(
                account_id=account.account_id.value,
                subscriber_code=account.subscriber_code,
                service_address_id=account.service_address_id,
                status=account.status,
            )
            for account in result.accounts
        ],
    )


def _subscriber_response(result: SubscriberReadModel) -> SubscriberResponse:
    return SubscriberResponse(
        subscriber_id=result.subscriber_id.value,
        first_name=result.first_name,
        last_name=result.last_name,
        date_of_birth=result.date_of_birth,
        citizenship=result.citizenship,
        accounts=[
            SubscriberAccountResponse(
                account_id=account.account_id.value,
                subscriber_code=account.subscriber_code,
                service_address_id=account.service_address_id,
                status=account.status,
            )
            for account in result.accounts
        ],
    )

