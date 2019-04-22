from mock import patch
from lms_connector.helpers import no_error


@patch('lms_connector.helpers.logger.exception')
def test_no_error(logger_mock):
    @no_error
    def some_func():
        raise Exception()
    some_func()
    assert logger_mock.call_count == 1
