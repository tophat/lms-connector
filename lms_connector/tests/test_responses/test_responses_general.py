from rest_framework.response import Response as DRFResponse
from rest_framework import status

from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    FormattedError,
    MultiLCResponse,
    LCResponse,
    SingleLCResponse,
)

# Mostly arbitrary values.
mock_code = ErrorResponseCodes.lms_data_invalid
mock_detail = 'Lielvārde'
mock_source = 'Ķegums'
mock_status = status.HTTP_400_BAD_REQUEST
mock_status_code = status.HTTP_101_SWITCHING_PROTOCOLS

formatted_error = FormattedError(
    source=mock_source,
    status=mock_status,
    code=mock_code,
    detail=mock_detail,
)


def test_inheritance():
    """
    Test inheritance of response classes.

    Inheriting from DRFResponse is particularly important because,
    for example, it is what causes self.data to be rendered correctly
    in the response.
    """

    response = LCResponse(status_code=mock_status_code)
    assert isinstance(response, DRFResponse)

    single_response = SingleLCResponse(status_code=mock_status_code, result={})
    assert isinstance(single_response, LCResponse)

    multi_response = MultiLCResponse(status_code=mock_status_code)
    assert isinstance(multi_response, LCResponse)

    error_response = ErrorLCResponse(status_code=mock_status_code)
    assert isinstance(error_response, LCResponse)


def test_single_response():
    some_result_dict = {'toronto': 'snow'}
    response = SingleLCResponse(
        status_code=mock_status_code,
        result=some_result_dict
    )
    assert response.data['result'] == some_result_dict
    assert 'results' not in response.data
    assert response.status_code == mock_status_code


def test_add_multi_response():
    response = MultiLCResponse(status_code=mock_status_code)
    some_result_dict = {'toronto': 'snow'}
    response.add_result(some_result_dict)
    assert response.data['results'] == [some_result_dict]
    assert 'result' not in response.data
    assert response.status_code == mock_status_code


def test_error_response():
    response = ErrorLCResponse(status_code=mock_status_code)
    response.add_error(formatted_error)
    assert response.data['errors'] == [formatted_error]
    assert response.status_code == mock_status_code


def test_error_response_shorthand():
    response = ErrorLCResponse(
        status_code=mock_status_code,
        errors=[formatted_error],
    )
    response.add_error(formatted_error)
    num_errors_expected = 2
    assert response.data['errors'] == [formatted_error] * num_errors_expected
    assert response.status_code == mock_status_code
