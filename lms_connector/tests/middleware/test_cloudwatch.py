from lms_connector.middleware.cloudwatch import CloudWatch
from mock import patch, MagicMock
from rest_framework.response import Response


def test_cloudwatch_status_mode_metric():
    status_code = 90210

    resp = Response()
    resp.status_code = status_code

    def get_response(resp):
        return resp

    with patch(
        'lms_connector.middleware.cloudwatch.boto3.client',
        autospec=True
    ) as boto3_mock, patch.dict(
        'os.environ', {'STAGE': 'funstage'},
    ):

        client_mock = MagicMock()

        boto3_mock.return_value = client_mock
        middleware = CloudWatch(get_response)
        middleware(resp)

        actual = client_mock.method_calls[0][2]['MetricData'][0]
        actual = actual['Dimensions'][0]['Value']

        assert actual == str(status_code)
