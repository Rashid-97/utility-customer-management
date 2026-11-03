from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from customer_management.api.schemas.responses import ErrorResponse
from customer_management.application.exceptions import (
    ApplicationError,
    ExternalServiceUnavailableError,
    OutstandingDebtError,
    SubscriberNotFoundError,
)
from customer_management.common.exceptions import (
    ActiveAccountAlreadyExistsError,
    AddressVerificationRejectedError,
    ApplicantUnderageError,
    DomainError,
    IdentityVerificationRejectedError,
    InvalidDomainValueError,
    SubscriberAccountAlreadyTerminatedError,
    SubscriberAccountNotFoundError,
    SubscriberCodeAlreadyExistsError,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(ApplicationError, _handle_application_error)
    app.add_exception_handler(IntegrityError, _handle_integrity_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)


async def _handle_domain_error(
    request: Request,
    error: DomainError,
) -> JSONResponse:
    del request
    status_code, code = _domain_error_details(error)
    return _error_response(status_code, code, str(error))


async def _handle_application_error(
    request: Request,
    error: ApplicationError,
) -> JSONResponse:
    del request
    if isinstance(error, SubscriberNotFoundError):
        return _error_response(status.HTTP_404_NOT_FOUND, "SUBSCRIBER_NOT_FOUND", str(error))
    if isinstance(error, OutstandingDebtError):
        return _error_response(status.HTTP_409_CONFLICT, "OUTSTANDING_DEBT", str(error))
    if isinstance(error, ExternalServiceUnavailableError):
        return _error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "EXTERNAL_SERVICE_UNAVAILABLE",
            str(error),
        )
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "APPLICATION_ERROR",
        "The operation could not be completed.",
    )


async def _handle_integrity_error(
    request: Request,
    error: IntegrityError,
) -> JSONResponse:
    del request, error
    return _error_response(
        status.HTTP_409_CONFLICT,
        "DATABASE_CONFLICT",
        "The requested change conflicts with existing data.",
    )


async def _handle_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    del request, error
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "REQUEST_VALIDATION_ERROR",
        "The request is invalid.",
    )


def _domain_error_details(error: DomainError) -> tuple[int, str]:
    if isinstance(error, SubscriberAccountNotFoundError):
        return status.HTTP_404_NOT_FOUND, "SUBSCRIBER_ACCOUNT_NOT_FOUND"
    if isinstance(error, ActiveAccountAlreadyExistsError):
        return status.HTTP_409_CONFLICT, "ACTIVE_ACCOUNT_ALREADY_EXISTS"
    if isinstance(error, SubscriberCodeAlreadyExistsError):
        return status.HTTP_409_CONFLICT, "SUBSCRIBER_CODE_ALREADY_EXISTS"
    if isinstance(error, SubscriberAccountAlreadyTerminatedError):
        return status.HTTP_409_CONFLICT, "SUBSCRIBER_ACCOUNT_ALREADY_TERMINATED"
    if isinstance(error, IdentityVerificationRejectedError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, "IDENTITY_VERIFICATION_REJECTED"
    if isinstance(error, AddressVerificationRejectedError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, "ADDRESS_VERIFICATION_REJECTED"
    if isinstance(error, ApplicantUnderageError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, "APPLICANT_UNDERAGE"
    if isinstance(error, InvalidDomainValueError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_DOMAIN_VALUE"
    return status.HTTP_422_UNPROCESSABLE_ENTITY, "DOMAIN_ERROR"


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    error = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
    )

