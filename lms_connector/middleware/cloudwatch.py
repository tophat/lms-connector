import boto3
import os
from datetime import datetime
from lms_connector.helpers import no_error


def get_cloud_watch_client():
    return boto3.client('cloudwatch')


def get_namespace():
    return f'lms-connector/{os.environ.get("STAGE")}'


@no_error
def record_response_status_code(status_code):
    if os.environ.get('STAGE') is None:
        # Probably local dev without a lambda, we don't need to log
        # response codes in this case.
        return
    status_code = int(status_code)
    now = datetime.utcnow()
    cw_client = get_cloud_watch_client()
    cw_client.put_metric_data(
        Namespace=get_namespace(),
        MetricData=[
            {
                'MetricName': 'response_codes',
                'Dimensions': [
                    {
                        'Name': 'response_codes',
                        'Value': str(status_code),
                    },
                ],
                'Timestamp': now,
                'Value': 1,
                'Unit': 'Count',
                'StorageResolution': 60
            },
        ]
    )


class CloudWatch:
    def __init__(self, get_response):
        # Middleware boilerplate
        self.get_response = get_response

    def __call__(self, request):
        # This is where the view ends up being called
        response = self.get_response(request)
        # The view has now been run and we have a response
        record_response_status_code(response.status_code)
        return response
