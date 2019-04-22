import logging

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated

from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    FormattedError,
)

logger = logging.getLogger(__name__)


def exception_handler(exc, context=None) -> ErrorLCResponse:
    if isinstance(exc, ErrorLCResponse):
        return exc
    elif isinstance(exc, NotAuthenticated):
        formatted_error = FormattedError(
            code=ErrorResponseCodes.not_authenticated,
            source='NotAuthenticated',
            detail=exc.detail,
            status=exc.status_code,
        )
        return ErrorLCResponse(
            status_code=exc.status_code,
            errors=[formatted_error],
        )
    else:
        logger.exception(exc)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        formatted_error = FormattedError(
            code=ErrorResponseCodes.unhandled_exception,
            source='exception_handler',
            detail=str(exc),
            status=status_code,
        )
        return ErrorLCResponse(
            status_code=status_code,
            errors=[formatted_error],
        )
