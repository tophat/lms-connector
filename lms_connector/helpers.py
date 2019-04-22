from rest_framework import status

from typing import (
    Dict,
    List,
)
from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    FormattedError,
)
from lms_connector.lms_connector_logger import logger

HEADERS_PROCESSOR = 'headers processor'


def no_error(func):
    # Swallow all uncaught errors
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
    return inner


def internal_header_to_external(internal_header: str) -> str:
    """
    Within our app we access headers in this form
    HTTP_LMS_TYPE but they are supplied like LMS-TYPE.

    This converts the internal form to the external form for error reporting
    purposes.
    """
    assert internal_header.startswith('HTTP_')
    assert '-' not in internal_header

    no_http = internal_header[5:]
    no_http_dashes = no_http.replace('_', '-')
    return no_http_dashes


def raise_for_missing_headers(
    incoming_headers: Dict,
    required_headers: List[str],
):
    errors = []
    for required_header in required_headers:
        if required_header not in incoming_headers:
            errors.append(FormattedError(
                source=HEADERS_PROCESSOR,
                code=ErrorResponseCodes.missing_required_header,
                detail=internal_header_to_external(required_header),
            ))

    if errors:
        raise ErrorLCResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=errors,
        )
