import pytest

from lms_connector.connectors.creds_envelope import CredsEnvelope
from lms_connector.connectors import abstract
from lms_connector.connectors.abstract import AbstractLMSConnector
from lms_connector.connectors.sakai import SakaiConnector
from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    ErrorResponseDetails,
)


def test_get_connector():
    """
    Test that we get back a connector from factory method.
    """
    creds_envelope = CredsEnvelope()
    connector = abstract.AbstractLMSConnector.get_connector(
        'sakai', lms_base_url='http://something'
    )
    assert isinstance(connector, SakaiConnector)


def test_get_non_existent_connector():
    """
    Test that we get back a connector from factory method.
    """
    bad_lms = 'I do not exist'
    with pytest.raises(ErrorLCResponse) as e:
        abstract.AbstractLMSConnector.get_connector(
            bad_lms,
            'http://something',
        )

    error = e.value.errors[0]
    assert error['source'] == 'get_connector'
    assert error['code'] == ErrorResponseCodes.unsupported_lms.value
    assert error['detail'] == ErrorResponseDetails.lms_not_supported(bad_lms)


def test_raise_thirdparty_error_on_error():
    """
    _raise_thirparty_error_on_error should raise error response.
    """
    url = '互联网'
    exception_str = '我们做得很糟糕'
    try:
        with AbstractLMSConnector._raise_thirdparty_error_on_error(url):
            raise Exception(exception_str)
    except ErrorLCResponse as e:
        error = e.errors[0]
        assert error['source'] == url
        assert error['code'] == ErrorResponseCodes.bad_thirdparty_request.value
        assert error['detail'] == exception_str
    else:
        assert False, "Error should have be raised."
