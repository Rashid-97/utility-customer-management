from pydantic import BaseModel, Field

from customer_management.domain.subscriber.identity_document import DocumentType


class RegisterSubscriberRequest(BaseModel):
    document_number: str = Field(min_length=1)
    document_type: DocumentType
    service_address_id: str = Field(min_length=1)
    city_code: str = Field(min_length=1)
    street_code: str = Field(min_length=1)
    building_code: str = Field(min_length=1)
    apartment_code: str = Field(min_length=1)


class CreateSubscriberAccountRequest(BaseModel):
    service_address_id: str = Field(min_length=1)
    city_code: str = Field(min_length=1)
    street_code: str = Field(min_length=1)
    building_code: str = Field(min_length=1)
    apartment_code: str = Field(min_length=1)

