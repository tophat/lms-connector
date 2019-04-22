from enum import Enum
import json
from json import JSONDecodeError
from typing import (
    List,
    Optional,
)

from rest_framework import status as drf_status_code
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class ErrorResponseCodes(Enum):
    """
    Provide structure to the FormattedError.code values
    """
    unsupported_lms = 'unsupported_lms'
    lms_data_bad_json = 'lms_data_bad_json'
    lms_data_invalid = 'lms_data_invalid'
    bad_thirdparty_request = 'bad_thirdparty_request'
    bad_lms_connector_headers = 'bad_lms_connector_headers'
    missing_required_header = 'missing_required_header'
    headers_not_set = 'headers_not_set'
    not_authenticated = 'not_authenticated'
    unhandled_exception = 'unhandled_exception'


class ErrorResponseDetails:
    """
    Provide structure to the FormattedError.status values
    """

    @staticmethod
    def header_missing(field_name):
        return f'{field_name} is a required header field'

    @staticmethod
    def lms_not_supported(lms_name: str) -> str:
        return 'LMS {} not supported.'.format(lms_name)

    @staticmethod
    def lms_data_not_json(decode_error: JSONDecodeError) -> str:
        return 'lms_data is not json: {}'.format(str(decode_error))


class FormattedError(dict):
    def __init__(
        self,
        source: str,
        code: ErrorResponseCodes,
        detail: str,
        status: Optional[int] = None,
    ):
        """
        Provide a well defined json serializable dictionary for all errors
        and individual error responses.

        This takes some inspiration from https://jsonapi.org/format/#errors

        :param source: Where did the error originate?
            e.x.
            - http://remotelms/courses/5/list_students
            - http://thisconnnector/courses/5/list_students
            - Sakai initialization
        :param code: an application-specific error code,
            expressed as a _string_ value.
        :param detail: a human-readable explanation specific to this
            occurrence of the problem.
            e.x. Cannot list students for course id 55 because course id 55
             does not exist
        :param status: A standard HTTP status code from the LMS. This is the
            code that is found in the response body, not to be confused
            with the actually http response status code found in the response
            header.
        """

        assert isinstance(code, ErrorResponseCodes)
        assert isinstance(status, int) or status is None

        super(FormattedError, self).__init__([
            ('source', source),
            ('code', code.value),
            ('detail', detail),
            ('status', status),
        ])

    def __lt__(self, other):
        return str(self) < str(other)

    def __eq__(self, other):
        return str(self) == str(other)


class LCResponse(Response):
    """
    All responses should inherit from this.
    """
    def __init__(self, status_code: drf_status_code):
        """
        :param status_code: http response status_code, not the status code
            found anywhere in the response body.
        """
        super(LCResponse, self).__init__(data={}, status=status_code)


class SingleLCResponse(LCResponse):
    """
    Use for endpoints that are intended to return a single result
    such as for an endpoint which GETs a single course.
    """
    def __init__(
            self,
            status_code: drf_status_code,
            result: dict,
    ):
        """
        :param status_code: http response status_code, not the status code
            found anywhere in the response body.
        :param result:
        """
        super(SingleLCResponse, self).__init__(status_code=status_code)
        self.data['result'] = result


class MultiLCResponse(LCResponse):
    """
    Use for endpoints that are intended to return multiple responses.
    The intention matters here, do not use for an endpoint which can
    get multiple responses but did not in a specific case.
    e.x. listing the students in a course.
    """
    def __init__(
            self,
            status_code: drf_status_code,
            results: List[dict] = None
    ):
        """
        :param status_code: http response status_code, not the status code
            found anywhere in the response body.
        :param results:
        """
        super(MultiLCResponse, self).__init__(status_code=status_code)
        self._results = results if results else []
        self.data['results'] = self._results

    def add_result(self, result) -> None:
        self._results.append(result)


class ErrorLCResponse(LCResponse, Exception):
    """
    Use when returning error(s).
    At this time no non-error response data will be included.
    """
    def __init__(
            self,
            status_code: drf_status_code,
            errors: List[FormattedError] = None,
    ):
        """
        :param status_code: http response status_code, not the status code
            found anywhere in the response body.
        :param errors: shorthand for calling add_error().
        """
        super(ErrorLCResponse, self).__init__(status_code=status_code)
        self._errors: List[FormattedError] = []
        self.data['errors'] = self._errors
        if errors:
            for error in errors:
                self.add_error(error)

    def add_error(self, error: FormattedError) -> None:
        self._errors.append(error)

    @property
    def errors(self):
        return self._errors

    @staticmethod
    def _field_name_error(field_name: str, field_error: str) -> str:
        """
        Provide a format for the detail field on serializer errors
        """
        return f'{field_name}: {field_error}'

    @classmethod
    def from_serializer_errors(
            cls,
            source: str,
            code: ErrorResponseCodes,
            serializer: Serializer,
            status_code: drf_status_code = (
                    drf_status_code.HTTP_400_BAD_REQUEST),
    ) -> 'ErrorLCResponse':
        """
        Create an error response based on drf serializer errors
        :param source: as found in lms_connector.responses.FormattedError
        :param code: as found in lms_connector.responses.FormattedError
        :param serializer: the drf serializer
        :param status_code: http status code (not in the response body)
        """
        error_responses = ErrorLCResponse(
            status_code=status_code,
        )
        for field_name, field_errors in serializer.errors.items():
            for field_error in field_errors:
                error_responses.add_error(FormattedError(
                    source=source,
                    code=code,
                    detail=cls._field_name_error(field_name, field_error),
                ))

        return error_responses

    def __str__(self):
        return json.dumps(self.errors)
