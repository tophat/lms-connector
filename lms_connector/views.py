from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import status
from lms_connector.responses import (
    MultiLCResponse,
    SingleLCResponse,
)
from urllib.parse import unquote
from lms_connector.entities import Grade

from lms_connector.connectors.abstract import AbstractLMSConnector


def connector(request: Request) -> AbstractLMSConnector:
    return AbstractLMSConnector.get_connector_from_request(request)


class AuthUrlView(APIView):
    required_headers = [
        'HTTP_LMS_TYPE',
        'HTTP_LMS_BASE_URL',
        'HTTP_LMS_CLIENT_KEY',
        'HTTP_LMS_CLIENT_SECRET',
    ]

    def get(self, request):
        auth_url_payload = connector(request).get_auth_url(
            request_token_url=request.GET['request_token_url'],
            authorize_url=request.GET['authorize_url'],
            callback_url=request.GET['callback_url'],
        )
        return Response(auth_url_payload)


class CurrentUserView(APIView):
    def get(self, request):
        return SingleLCResponse(
            status_code=status.HTTP_200_OK,
            result=connector(request).get_current_user_info(),
        )


class CoursesView(APIView):
    def get(self, request):
        courses = connector(request).list_courses()
        return MultiLCResponse(
            status_code=status.HTTP_200_OK,
            results=courses,
        )


class EnrollmentsView(APIView):
    def get(self, request, lms_course_id: str):
        students = connector(request).list_students_in_course(lms_course_id)
        return MultiLCResponse(
            status_code=status.HTTP_200_OK,
            results=students,
        )


class AssignmentView(APIView):
    def get(self, request, lms_course_id: str, lms_assignment_id: str):
        lms_assignment_id = unquote(lms_assignment_id)
        lms_column = connector(request).get_assignment(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
        )
        return SingleLCResponse(
            status_code=status.HTTP_200_OK,
            result=lms_column,
        )

    def post(self, request, lms_course_id: str, lms_assignment_id: str):
        lms_assignment_id = unquote(lms_assignment_id)
        assignment = connector(request).post_assignment(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
            max_grade=request.data.get('max_grade'),
            external_assignment_id=request.data.get('external_assignment_id'),
        )
        return SingleLCResponse(
            status_code=status.HTTP_200_OK,
            result=assignment,
        )

    def put(self, request, lms_course_id: str, lms_assignment_id: str):
        lms_assignment_id = unquote(lms_assignment_id)
        assignment = connector(request).update_assignment(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
            max_grade=request.data.get('max_grade'),
            external_assignment_id=request.data.get('external_assignment_id'),
        )
        return SingleLCResponse(
            status_code=status.HTTP_200_OK,
            result=assignment,
        )


class GradesView(APIView):
    def post(self, request, lms_course_id: str, lms_assignment_id: str):
        lms_assignment_id = unquote(lms_assignment_id)
        grades = []
        for grade_info in request.data['grades']:
            grades.append(Grade(
                lms_student_id=grade_info['lms_student_id'],
                grade=grade_info['grade'],
            ))

        assignment = connector(request).post_grades(
            lms_course_id=lms_course_id,
            lms_assignment_id=lms_assignment_id,
            max_grade=request.data.get('max_grade'),
            student_grade_info=grades,
            external_assignment_id=request.data.get('external_assignment_id'),
        )
        return SingleLCResponse(
            status_code=status.HTTP_200_OK,
            result=assignment,
        )


class DjangoTestEndpoint(APIView):
    """
    The default endpoint for lms-connector, i.e. /
    """
    def get(self, request, format=None):
        content = {'healthy': u'\U0001F4AF'}
        return Response(content)
