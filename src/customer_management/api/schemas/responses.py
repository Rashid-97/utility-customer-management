from datetime import date
from uuid import UUID

from pydantic import BaseModel


class SubscriberAccountResponse(BaseModel):
    account_id: UUID
    subscriber_code: str
    service_address_id: str
    status: str


class SubscriberResponse(BaseModel):
    subscriber_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    citizenship: str
    accounts: list[SubscriberAccountResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str

