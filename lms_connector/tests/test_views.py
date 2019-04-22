import pytest
from django.test import Client
from django.urls import reverse
from django.test.utils import override_settings
from mock import patch, MagicMock
from rest_framework import status
from urllib.parse import (
    quote,
    urljoin,
)
import requests
import requests_mock

from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    ErrorResponseDetails,
    FormattedError,
)
from lms_connector.tests import fixtures
from lms_connector.tests.helpers import spy_on
from lms_connector.entities import Role
from lms_connector.connectors import sakai
from lms_connector import helpers


TEST_API_KEY = 'TEST_API_KEY'


"""
HELPERS
"""


def assert_headers(headers_dict, request_mock: requests_mock.Mocker):
    auth_str = (
        request_mock.request_history[0]
        .headers['Authorization'].decode("utf-8")
    )
    auth_dict = {}

    # The authorization ends up being a bytes string, parse out the info.
    # The existence of a built in way to do this was not known at the
    # time of writing.
    for key_val_pair_str in auth_str.split(','):
        key, value = key_val_pair_str.split('=', 1)
        key = key.strip()
        # Would fail if actual value starts/ends with legit ' or "
        value = value.strip('"').strip("'").strip()
        auth_dict[key] = value

    assert (
            auth_dict['oauth_consumer_key'] ==
            headers_dict['HTTP_LMS_CLIENT_KEY']
    )
    assert (
            auth_dict['oauth_token'] ==
            headers_dict['HTTP_LMS_OAUTH_TOKEN']
    )


"""
TESTS
"""


def _test_correct_api_key_is_required(url, method, api_key):
    client = Client()
    requester = getattr(client, method)
    resp = requester(url, HTTP_API_KEY='invalid-api-key')

    # Incorrect API key should return 403
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()['errors'] == [
        {
            'code': 'not_authenticated',
            'detail': 'Authentication credentials were not provided.',
            'source': 'NotAuthenticated',
            'status': 403,
        },
    ]

    resp = requester(url, HTTP_API_KEY=api_key)
    # Correct API key should return anything but 403
    assert resp.status_code != status.HTTP_403_FORBIDDEN


@override_settings(API_KEY=TEST_API_KEY)
@pytest.mark.parametrize('view_name,kwargs,method', [
    ('auth_url', {}, 'get'),
    ('current_user', {}, 'get'),
    ('courses', {}, 'get'),
    ('course_enrollments', {'lms_course_id': 1}, 'get'),
    ('assignments', {'lms_course_id': 1, 'lms_assignment_id': 1}, 'get'),
    ('grades', {'lms_course_id': 1, 'lms_assignment_id': 1}, 'post'),
    ('django_test', {}, 'get'),

])
def test_urls_are_authenticated(view_name, kwargs, method):
    url = reverse(view_name, kwargs=kwargs)
    _test_correct_api_key_is_required(url, method, TEST_API_KEY)


def test_root_url():
    client = Client()
    response = client.get('/')
    assert response.json() == {'healthy': u'\U0001F4AF'}


@patch('lms_connector.connectors.sakai.OAuth1Session', autospec=True)
def test_sakai_auth_url(oauth_mock):
    """
    Test auth url retrieval for Sakai.

    Test that we can retrieve a formatted Oauth1 URL for Sakai
    """
    def mock_fetch_token(mock_oauth_token, mock_oauth_token_secret):
        def mock_token_getter(mock_url):
            return {
                'oauth_token': mock_oauth_token,
                'oauth_token_secret': mock_oauth_token_secret,
            }
        return mock_token_getter

    mock_authorize_url = 'http://host/oauth-tool/authorize/'
    another_mock = MagicMock()
    another_mock.fetch_request_token.side_effect = mock_fetch_token(
        fixtures.oauth_creds_dict['HTTP_LMS_OAUTH_TOKEN'],
        fixtures.oauth_creds_dict['HTTP_LMS_OAUTH_SECRET'],
    )
    oauth_mock.return_value = another_mock

    data = {
        'request_token_url': 'http://host/oauth-tool/request_tokén',
        'authorize_url': mock_authorize_url,
        'callback_url': "http://this.doesnt.ma/tter",
    }
    headers = fixtures.get_mocked_headers('http://somebaseurl')
    del headers['HTTP_LMS_OAUTH_TOKEN']
    del headers['HTTP_LMS_OAUTH_SECRET']

    client = Client()
    resp = client.get(
        reverse('auth_url'),
        content_type='application/json',
        data=data,
        **headers,
    )

    expected_auth_url = (
        f'{mock_authorize_url}'
        f'?oauth_token={fixtures.oauth_creds_dict["HTTP_LMS_OAUTH_TOKEN"]}'
    )
    assert resp.status_code == status.HTTP_200_OK

    actual_resp_json = resp.json()
    expected_resp_json = {
        'auth_url': expected_auth_url,
        'redirect_key': 'redirect_uri',
        'oauth_token_secret': fixtures.oauth_creds_dict[
            'HTTP_LMS_OAUTH_SECRET'
        ],
    }
    assert actual_resp_json == expected_resp_json


def test_bad_lms_type_raises_error():
    """
    Test error raised with non real lms.
    """
    fake_lms = 'This LMS does not exist'
    expected_formatted_error = FormattedError(
        source='get_connector',
        code=ErrorResponseCodes.unsupported_lms,
        detail=ErrorResponseDetails.lms_not_supported(fake_lms),
    )
    mocked_headers = fixtures.get_mocked_headers('http://something')
    mocked_headers['HTTP_LMS_TYPE'] = fake_lms
    client = Client()
    resp = client.get(
        reverse('courses'),
        content_type='application/json',
        **mocked_headers,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()['errors'] == [expected_formatted_error]


def test_list_courses():
    mocked_lms_base_url = 'http://jjjjjjjj'
    mocked_resource = sakai.COURSES_RESOURCE
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)
    mocked_status_code = status.HTTP_200_OK
    mocked_headers = fixtures.get_mocked_headers(
        lms_base_url=mocked_lms_base_url,
    )

    mock_title_1 = '학교는 재미있다'
    mock_id_1 = 'someid1'
    mock_title_2 = 'course title 2'
    mock_id_2 = 'someid2'
    mock_title_no_sites = 'mock title no sites'
    mock_title_no_gradebook = 'course title no gradebook'
    mocked_sakai_response = {
        'site_collection': [
            {
                'id': mock_id_1,
                'title': mock_title_1,
                'sitePages': [{'title': 'Gradebook'}]
            },
            {
                'id': mock_id_2,
                'title': mock_title_2,
                'sitePages': [
                    {'title': 'naaa'},
                    {'title': 'Gradebook'}
                ]
            },
            {
                'title': mock_title_no_gradebook,
                'sitePages': [{'title': 'NOPE'}]
            },
            {'title': mock_title_no_sites},
        ]
    }
    expected = {
        'results': [
            {'course_id': mock_id_1, 'title': mock_title_1},
            {'course_id': mock_id_2, 'title': mock_title_2},
        ]
    }

    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.get(
            mocked_url,
            status_code=mocked_status_code,
            json=mocked_sakai_response,

        )
        resp = client.get(
            reverse('courses'),
            **mocked_headers
        )
    assert resp.json() == expected
    assert_headers(mocked_headers, http_mock)


def test_list_students_in_course():
    mocked_lms_base_url = 'http://jjjjjjjj'
    mock_course_id = 'somecourseid'
    mocked_resource = sakai.STUDENTS_RESOURCE.format(
        lms_course_id=mock_course_id
    )
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)
    mocked_status_code = status.HTTP_200_OK
    mocked_headers = fixtures.get_mocked_headers(
        lms_base_url=mocked_lms_base_url
    )

    mock_student_id_1 = 'طالب علم'
    mock_student_email_1 = 'étudiant@étudiant.com'
    mock_student_first_name_1 = 'mock_student_first_name_1'
    mock_student_last_name_1 = 'mock_student_last_name_1'
    mock_student_user_name_1 = 'mock_student_user_name_1'

    mock_student_id_2 = 'mock student 2'
    mock_student_email_2 = 'mockstudent@two.com'
    mock_student_first_name_2 = 'mock_student_first_name_2'
    mock_student_last_name_2 = 'mock_student_last_name_2'
    mock_student_user_name_2 = 'mock_student_user_name_2'

    mocked_sakai_response = {
        'grades_collection': [
            {
                'userId': mock_student_id_1,
                'email': mock_student_email_1,
                'role': Role.student.value,
                'fname': mock_student_first_name_1,
                'lname': mock_student_last_name_1,
                'username': mock_student_user_name_1,
            },
            {
                'userId': mock_student_id_2,
                'email': mock_student_email_2,
                'role': Role.student.value,
                'fname': mock_student_first_name_2,
                'lname': mock_student_last_name_2,
                'username': mock_student_user_name_2,
            },
        ]
    }
    expected = {
        'results': [
            {
                'student_id': mock_student_id_1,
                'email': mock_student_email_1,
                'role': Role.student.value,
                'first_name': mock_student_first_name_1,
                'last_name': mock_student_last_name_1,
                'user_name': mock_student_user_name_1,
            },
            {
                'student_id': mock_student_id_2,
                'email': mock_student_email_2,
                'role': Role.student.value,
                'first_name': mock_student_first_name_2,
                'last_name': mock_student_last_name_2,
                'user_name': mock_student_user_name_2,
            },
        ]
    }

    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.get(
            mocked_url,
            status_code=mocked_status_code,
            json=mocked_sakai_response,

        )
        resp = client.get(
            reverse(
                'course_enrollments',
                kwargs={'lms_course_id': mock_course_id}
            ),
            **mocked_headers
        )
    assert resp.json() == expected
    assert_headers(mocked_headers, http_mock)


def test_get_current_user():
    mocked_lms_base_url = 'http://jjjjjjjj'
    mocked_resource = sakai.CURRENT_USER_RESOURCE
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)
    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.get(
            mocked_url,
            status_code=status.HTTP_200_OK,
            json=fixtures.current_user_response,
        )
        resp = client.get(
            reverse(
                'current_user',
            ),
            **fixtures.get_mocked_headers(mocked_lms_base_url)
        )
    expected = {
        'result': {
            'lms_user_id': fixtures.current_user_response['id'],
            'email': fixtures.current_user_response['email'],
            'first_name': fixtures.current_user_response['firstName'],
            'last_name': fixtures.current_user_response['lastName'],
        }
    }
    assert resp.json() == expected
    assert resp.status_code == status.HTTP_200_OK


def test_get_assignment():
    """
    Test getting an assignment.

    Submit a quoted assignment id to the lms connector, and observe
    that we call requests.get() using the unquoted version.

    We mock the quoted version because requests.get() will automatically
    quote the assignment id.
    """
    mocked_lms_base_url = 'http://jjjjjjjj'
    mock_lms_course_id = 'mock_lms_course_id'
    mock_lms_assignment_id = 'mock lms assignment id'
    mock_lms_assignment_id_quoted = quote(mock_lms_assignment_id)

    # When the get request is made, the get itself will quote the
    # assignment id.
    mocked_resource_quoted = sakai.ASSIGNMENT_RESOURCE.format(
        lms_course_id=mock_lms_course_id,
        lms_assignment_id=mock_lms_assignment_id_quoted,
    )
    mocked_url_quoted = urljoin(mocked_lms_base_url, mocked_resource_quoted)

    mocked_resource = sakai.ASSIGNMENT_RESOURCE.format(
        lms_course_id=mock_lms_course_id,
        lms_assignment_id=mock_lms_assignment_id,
    )
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)

    requests.get = spy_on(requests.get)

    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.get(
            mocked_url_quoted,
            status_code=status.HTTP_200_OK,
            json=fixtures.sakai_get_assignment_response,
        )
        resp = client.get(
            reverse(
                'assignments',
                kwargs={
                    'lms_course_id': mock_lms_course_id,
                    'lms_assignment_id': mock_lms_assignment_id_quoted,
                },
            ),
            **fixtures.get_mocked_headers(mocked_lms_base_url)
        )
    expected = {
        'result': {
            'title': fixtures.sakai_get_assignment_response['name'],
            'max_grade':
                fixtures.sakai_get_assignment_response['pointsPossible'],
        }
    }
    assert resp.json() == expected
    assert resp.status_code == status.HTTP_200_OK

    # Check that we called get with the unquoted resource
    actual_get_url = requests.get.mock.call_args_list[0][0][0]
    assert actual_get_url == mocked_url


def test_post_grade():
    """
    Test posting an assignment.

    Via the URL submit a quoted assignment id, observe the unquoted
    version in the body sent to the mock.
    """
    mock_lms_assignment_id = 'mock lms assignment id'
    mock_lms_assignment_id_quoted = quote(mock_lms_assignment_id)
    assert '%20' in mock_lms_assignment_id_quoted
    expected_post_to_sakai = {
        'name': mock_lms_assignment_id,
        'externalID': 'sssssssssssdddddd',
        'pointsPossible': '100',
        'scores': [{
            'userId': '08f72871-4f03-4d76-8de6-eb35aba9f8f4',
            'grade': '72'
        }]}

    expected_response_from_connector = {
        "result": {
            # In reality 'title' would be the 'lms_assigment_id' but given we
            # are not testing a sakai sever they are not related as far
            # as this unit test is concerned.
            "title": "thinsusssslateONEMOREE",
            "max_grade": 100,
            "grades": [
                {
                    "lms_student_id": "08f72871-4f03-4d76-8de6-eb35aba9f8f4",
                    "grade": "72"
                }
            ]
        }
    }

    mocked_lms_base_url = 'http://jjjjjjjj'
    mock_lms_course_id = 'mock_lms_course_id'
    mocked_resource_quoted = sakai.SCORES_RESOURCE.format(
        lms_course_id=mock_lms_course_id,
    )
    mocked_url_quoted = urljoin(mocked_lms_base_url, mocked_resource_quoted)
    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.post(
            mocked_url_quoted,
            status_code=status.HTTP_200_OK,
            json=fixtures.sakai_post_grade_response,
        )
        resp = client.post(
            reverse(
                'grades',
                kwargs={
                    'lms_course_id': mock_lms_course_id,
                    'lms_assignment_id': mock_lms_assignment_id_quoted,
                },
            ),
            content_type='application/json',
            data=fixtures.sakai_post_grade_data,
            **fixtures.get_mocked_headers(mocked_lms_base_url)
        )

        assert http_mock.request_history[0].json() == expected_post_to_sakai
        assert resp.json() == expected_response_from_connector


def test_put_assignment():
    """
    Test putting an assignment.

    Via the URL submit a quoted assignment id, observe the unquoted
    version in the body sent to the mock.
    """
    mock_lms_assignment_id = 'mock lms assignment id'
    mock_lms_assignment_id_quoted = quote(mock_lms_assignment_id)
    assert '%20' in mock_lms_assignment_id_quoted
    expected_post_to_sakai = {
        'name': mock_lms_assignment_id,
        'externalID': 'sssssssssssdddddd',
        'pointsPossible': '100',
        'scores': [],
    }

    expected_response_from_connector = {
        "result": {
            "title": "thinsusssslateONEMOREE",
            "max_grade": 100,
        }
    }

    mocked_lms_base_url = 'http://jjjjjjjj'
    mock_lms_course_id = 'mock_lms_course_id'
    mocked_resource = sakai.SCORES_RESOURCE.format(
        lms_course_id=mock_lms_course_id,
    )
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)
    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.post(
            mocked_url,
            status_code=status.HTTP_200_OK,
            json=fixtures.sakai_post_assignment_response,
        )
        resp = client.put(
            reverse(
                'assignments',
                kwargs={
                    'lms_course_id': mock_lms_course_id,
                    'lms_assignment_id': mock_lms_assignment_id_quoted,
                },
            ),
            content_type='application/json',
            data=fixtures.sakai_post_assignment_data,
            **fixtures.get_mocked_headers(mocked_lms_base_url)
        )

        assert http_mock.request_history[0].json() == expected_post_to_sakai
        assert resp.json() == expected_response_from_connector


def test_post_assignment():
    """
    Test posting an assignment to Sakai.

    We submit a quoted assignment id via the URL and check that the
    unquoted version is in the body posted to the mock.
    """
    mock_lms_assignment_id = 'mock lms assignment id'
    mock_lms_assignment_id_quoted = quote(mock_lms_assignment_id)
    assert '%20' in mock_lms_assignment_id_quoted
    expected_post_to_sakai = {
        'name': mock_lms_assignment_id,
        'externalID': 'sssssssssssdddddd',
        'pointsPossible': '100',
        'scores': [],
    }

    expected_response_from_connector = {
        "result": {
            "title": "thinsusssslateONEMOREE",
            "max_grade": 100,
        }
    }

    mocked_lms_base_url = 'http://jjjjjjjj'
    mock_lms_course_id = 'mock_lms_course_id'
    mocked_resource = sakai.SCORES_RESOURCE.format(
        lms_course_id=mock_lms_course_id,
    )
    mocked_url = urljoin(mocked_lms_base_url, mocked_resource)
    with requests_mock.Mocker() as http_mock:
        client = Client()
        http_mock.post(
            mocked_url,
            status_code=status.HTTP_200_OK,
            json=fixtures.sakai_post_assignment_response,
        )
        resp = client.post(
            reverse(
                'assignments',
                kwargs={
                    'lms_course_id': mock_lms_course_id,
                    'lms_assignment_id': mock_lms_assignment_id_quoted,
                },
            ),
            content_type='application/json',
            data=fixtures.sakai_post_assignment_data,
            **fixtures.get_mocked_headers(mocked_lms_base_url)
        )

        assert http_mock.request_history[0].json() == expected_post_to_sakai
        assert resp.json() == expected_response_from_connector


def test_required_get_auth_headers():
    """
    Test error response from missing auth headers.
    """
    mock_authorize_url = 'http://host/oauth-tool/authorize/'
    data = {
        'request_token_url': 'http://host/oauth-tool/request_tokén',
        'authorize_url': mock_authorize_url,
        'callback_url': "http://this.doesnt.ma/tter",
    }
    headers = {
        header_key: header_val
        for header_key, header_val,
        in fixtures.get_mocked_headers('http://somebaseurl').items()
        if header_key == 'HTTP_LMS_TYPE'
    }

    client = Client()
    resp = client.get(
        reverse('auth_url'),
        content_type='application/json',
        data=data,
        **headers,
    )
    expected_errors = []
    for required_header in sakai.AUTH_REQUIRED_HEADERS:
        expected_errors.append(FormattedError(
            source=helpers.HEADERS_PROCESSOR,
            code=ErrorResponseCodes.missing_required_header,
            detail=helpers.internal_header_to_external(required_header)
        ))
    expected_error_response = ErrorLCResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=expected_errors,
    )
    assert resp.data == expected_error_response.data


@pytest.mark.parametrize('http_method,endpoint,endpoint_kwargs', [
    ('get', 'courses', {}),
    ('post', 'assignments', {'lms_course_id': '-', 'lms_assignment_id': '-'}),
])
def test_required_headers_via_get(http_method, endpoint, endpoint_kwargs):
    mocked_lms_base_url = 'http://jjjjjjjj'
    headers = {
        header_key: header_val
        for header_key, header_val,
        in fixtures.get_mocked_headers(mocked_lms_base_url).items()
        if header_key == 'HTTP_LMS_TYPE'
    }

    client = Client()
    resp = getattr(client, http_method)(
        reverse(
            endpoint,
            kwargs=endpoint_kwargs,
        ),
        content_type='application/json',
        **headers,
    )
    expected_errors = []
    for required_header in sakai.DEFAULT_REQUIRED_HEADERS:
        expected_errors.append(FormattedError(
            source=helpers.HEADERS_PROCESSOR,
            code=ErrorResponseCodes.missing_required_header,
            detail=helpers.internal_header_to_external(required_header)
        ))
    expected_error_response = ErrorLCResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=expected_errors,
    )
    assert resp.data == expected_error_response.data
