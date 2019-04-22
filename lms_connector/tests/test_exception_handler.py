from django.test import Client
from django.test.utils import override_settings
from django.urls import path, reverse
from rest_framework import status
from rest_framework.views import APIView

from lms_connector.tests import fixtures
from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    FormattedError,
)

mock_source = 'uＮɩτＴéႽτ'
mock_status = status.HTTP_400_BAD_REQUEST
mock_status_code = status.HTTP_206_PARTIAL_CONTENT
mock_code = ErrorResponseCodes.lms_data_invalid
mock_detail = 'Jēkabpils'
mock_formatted_error = FormattedError(
    source=mock_source,
    status=mock_status,
    code=mock_code,
    detail=mock_detail,
)


class ExceptionHandlerTestEndpoint(APIView):
    def get(self, _):
        error_response = ErrorLCResponse(
            status_code=mock_status_code,
            errors=[mock_formatted_error]
        )

        error_response.add_error(mock_formatted_error)

        raise error_response


urlpatterns = [
    path(
        'test_exception_handler',
        ExceptionHandlerTestEndpoint.as_view(),
        name='test_exception_handler'
    ),
]


@override_settings(ROOT_URLCONF=__name__)
def test_exception_handler():
    """
    Test that you can _raise_ an ErrorLCResponse and have it returned.
    """
    num_expected_errors = 2
    client = Client()
    resp = client.get(
        reverse('test_exception_handler'),
        content_type='application/json',
        **fixtures.get_mocked_headers('http://somebase'),
    )

    actual_errors = resp.json()['errors']
    assert len(actual_errors) == num_expected_errors
    assert actual_errors == [mock_formatted_error] * num_expected_errors
    assert resp.status_code == mock_status_code
