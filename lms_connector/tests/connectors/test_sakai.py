from lms_connector.connectors.sakai import SakaiConnector
from lms_connector.tests.fixtures import (
    sample_html_error_message_page,
    sample_html_error_message,
)


def test_parse_html_error():
    assert (
        SakaiConnector.get_error(sample_html_error_message_page)
        == sample_html_error_message
    )


def test_parse_non_html_error():
    sample_text = "blah blah blah"
    assert SakaiConnector.get_error(sample_text) == sample_text
