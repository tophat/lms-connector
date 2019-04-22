from typing import Dict, List, Union, Optional
from urllib.parse import urljoin

from requests_oauthlib import OAuth1, OAuth1Session
import re
import requests

from lms_connector.helpers import (
    raise_for_missing_headers,
)
from lms_connector.connectors.abstract import (
    AbstractLMSConnector,
)
from lms_connector.entities import (
    Assignment,
    Course,
    Grade,
    LMSUser,
    Role,
    Student,
)

COURSES_RESOURCE = 'direct/site.json'
STUDENTS_RESOURCE = 'direct/grades/students/{lms_course_id}.json'
CURRENT_USER_RESOURCE = 'direct/user/current.json'
ASSIGNMENT_RESOURCE = (
    'direct/grades/gradeitem/{lms_course_id}/{lms_assignment_id}.json'
)
SCORES_RESOURCE = 'direct/grades/gradeitem/{lms_course_id}.json'

HTTP_LMS_CLIENT_KEY = 'HTTP_LMS_CLIENT_KEY'
HTTP_LMS_CLIENT_SECRET = 'HTTP_LMS_CLIENT_SECRET'
AUTH_REQUIRED_HEADERS = [
    HTTP_LMS_CLIENT_KEY,
    HTTP_LMS_CLIENT_SECRET,
]
DEFAULT_REQUIRED_HEADERS = [
    'HTTP_LMS_BASE_URL',
    'HTTP_LMS_CLIENT_KEY',
    'HTTP_LMS_OAUTH_TOKEN',
]


class SakaiConnector(AbstractLMSConnector):
    @staticmethod
    def _get_oauth_auth(
        incoming_headers: Dict,
    ) -> OAuth1:

        return OAuth1(
            client_key=incoming_headers.get('HTTP_LMS_CLIENT_KEY'),
            client_secret=incoming_headers.get('HTTP_LMS_CLIENT_SECRET'),
            resource_owner_key=incoming_headers.get('HTTP_LMS_OAUTH_TOKEN')
        )

    @classmethod
    def _get_full_url(cls, hostname: str, resource: str) -> str:
        return urljoin(hostname, resource)

    @classmethod
    def _get(
        cls,
        incoming_request_headers: Dict,
        hostname: str,
        resource: str,
    ) -> Union[List[Dict], Dict]:
        """
        Wrap requests.get(), add credentials, and format url.
        """

        raise_for_missing_headers(
            incoming_request_headers,
            DEFAULT_REQUIRED_HEADERS,
        )

        auth = cls._get_oauth_auth(
            incoming_request_headers,
        )
        full_url = cls._get_full_url(hostname, resource)

        with cls._raise_thirdparty_error_on_error(full_url):
            request_response = requests.get(full_url, auth=auth)
            response_json = request_response.json()

        return response_json

    @staticmethod
    def get_error(response_text: str):
        message_pattern = r'.*(?<=<p><b>Message<\/b> )(.*?)(?=<\/p>).*'
        match = re.match(message_pattern, response_text)
        if match:
            return match.group(1)
        else:
            return response_text

    @classmethod
    def _post(
        cls,
        incoming_request_headers: Dict,
        hostname: str,
        resource: str,
        json: dict,
    ) -> Union[List[Dict], Dict]:
        """
        Wrap requests.post(), add credentials, data, and format url.
        """
        raise_for_missing_headers(
            incoming_request_headers,
            DEFAULT_REQUIRED_HEADERS,
        )
        auth = cls._get_oauth_auth(incoming_request_headers,)
        full_url = cls._get_full_url(hostname, resource)

        with cls._raise_thirdparty_error_on_error(full_url):
            request_response = requests.post(full_url, auth=auth, json=json)
            response_json = request_response.json()

        return response_json

    def get_auth_url(
        self,
        request_token_url: str,
        authorize_url: str,
        callback_url: str,
    ) -> Dict:

        raise_for_missing_headers(
            self.incoming_request_headers,
            AUTH_REQUIRED_HEADERS,
        )

        oauth = OAuth1Session(
            client_key=self.incoming_request_headers[HTTP_LMS_CLIENT_KEY],
            client_secret=(
                self.incoming_request_headers[HTTP_LMS_CLIENT_SECRET]),
            signature_type='auth_header',
            callback_uri=callback_url,
        )
        request_token = oauth.fetch_request_token(request_token_url)

        auth_url = (
            f'{authorize_url}'
            f'?oauth_token={request_token["oauth_token"]}'
        )
        return {
            'auth_url': auth_url,
            'redirect_key': 'redirect_uri',
            'oauth_token_secret': request_token.get('oauth_token_secret'),
        }

    def list_courses(self) -> List[Course]:
        courses_response = self._get(
            self.incoming_request_headers,
            self.lms_base_url,
            COURSES_RESOURCE,
        )
        courses = []
        for site in courses_response['site_collection']:
            pages = site.get('sitePages', [])
            for page in pages:
                # Only allow courses using the Gradebook feature.
                if page['title'] == 'Gradebook':
                    courses.append(Course(
                        course_id=site['id'],
                        title=site['title']
                    ))
                    break
        return courses

    def list_students_in_course(
        self,
        lms_course_id: str,
        course_sections: Optional[List[str]] = None
    ):
        students_response: List[Dict] = self._get(
            self.incoming_request_headers,
            self.lms_base_url,
            STUDENTS_RESOURCE.format(lms_course_id=lms_course_id),
        )['grades_collection']

        students = []
        for student in students_response:
            students.append(Student(
                student_id=student['userId'],
                email=student['email'],
                role=Role.student,
                first_name=student['fname'],
                last_name=student['lname'],
                user_name=student['username'],
            ))
        return students

    def get_current_user_info(self) -> LMSUser:
        resp = self._get(
            self.incoming_request_headers,
            self.lms_base_url,
            CURRENT_USER_RESOURCE,
        )
        return LMSUser(
            lms_user_id=resp['id'],
            email=resp['email'],
            first_name=resp.get('firstName'),
            last_name=resp.get('lastName'),
        )

    def get_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
    ):
        # lms_assignment_id for sakai is the assignment name
        resp = self._get(
            self.incoming_request_headers,
            self.lms_base_url,
            ASSIGNMENT_RESOURCE.format(
                lms_course_id=lms_course_id,
                lms_assignment_id=lms_assignment_id,
            ),
        )
        return Assignment(
            title=resp.get('name'),
            max_grade=resp.get('pointsPossible'),
        )

    def post_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        external_assignment_id: str = None
    ):
        assignment = self.post_grades(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
            max_grade=max_grade,
            student_grade_info=[],
            external_assignment_id=external_assignment_id,
        )
        if assignment.get('grades'):
            del assignment['grades']
        return assignment

    def update_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        external_assignment_id: str = None
    ):
        assignment = self.post_grades(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
            max_grade=max_grade,
            student_grade_info=[],
            external_assignment_id=external_assignment_id,
        )
        if assignment.get('grades'):
            del assignment['grades']
        return assignment

    def post_grades(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        student_grade_info: List[Grade],
        external_assignment_id: str = None,
    ) -> Assignment:

        sakai_grade_info = []
        for grade_info in student_grade_info:
            sakai_grade_info.append({
                'userId': grade_info['lms_student_id'],
                'grade': grade_info['grade'],
            })

        # lms_assignment_id for sakai is the assignment name
        payload = {
            'name': lms_assignment_id,
            'externalID': external_assignment_id,
            'pointsPossible': max_grade,
            'scores': sakai_grade_info,
        }
        resp = self._post(
            self.incoming_request_headers,
            self.lms_base_url,
            SCORES_RESOURCE.format(
                lms_course_id=lms_course_id,
            ),
            json=payload,
        )

        grades = []
        for grade_info in resp.get('scores', []):
            grades.append(Grade(
                lms_student_id=grade_info.get('userId'),
                grade=grade_info.get('grade')
            ))

        return Assignment(
            title=resp.get('name'),
            max_grade=resp.get('pointsPossible'),
            grades=grades,
        )
