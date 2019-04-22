from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from rest_framework.request import Request
from typing import Dict, List, Union, Optional
import traceback

from lms_connector.responses import (
    ErrorLCResponse,
    ErrorResponseCodes,
    ErrorResponseDetails,
    FormattedError,
)
from lms_connector.entities import (
    Assignment,
    Course,
    LMSUser,
    Student,
)
from lms_connector.lms_connector_logger import logger
from rest_framework import status


class AbstractLMSConnector:
    __metaclass__ = ABCMeta
    _incoming_request_headers: Union[Dict, None] = None

    @property
    def incoming_request_headers(self) -> Dict:
        if self._incoming_request_headers is not None:
            return self._incoming_request_headers
        else:
            # This would be a programming error, a user should not be able
            # to cause this.
            formatted_error = FormattedError(
                source='incoming request headers property',
                code=ErrorResponseCodes.headers_not_set,
                detail='headers were accessed without being set.'
            )
            raise ErrorLCResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors=[formatted_error]
            )

    @staticmethod
    def get_connector(
        lms_type: str,
        lms_base_url: str,
    ) -> 'AbstractLMSConnector':
        if lms_type == 'sakai':
            from lms_connector.connectors.sakai import SakaiConnector
            connector = SakaiConnector
        else:
            formatted_error = FormattedError(
                source='get_connector',
                code=ErrorResponseCodes.unsupported_lms,
                detail=ErrorResponseDetails.lms_not_supported(
                    str(lms_type)
                ),
            )
            raise ErrorLCResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=[formatted_error],
            )
        return connector(
            lms_base_url=lms_base_url,
        )

    @staticmethod
    def get_connector_from_request(
        request: Request
    ) -> 'AbstractLMSConnector':
        lms_base_url = request.META.get('HTTP_LMS_BASE_URL')
        lms_type = request.META.get('HTTP_LMS_TYPE')
        lms_connector = AbstractLMSConnector.get_connector(
            lms_type,
            lms_base_url,
        )
        lms_connector._incoming_request_headers = request.META
        return lms_connector

    def __init__(self, lms_base_url: str):
        self.lms_base_url = lms_base_url

    @classmethod
    @contextmanager
    def _raise_thirdparty_error_on_error(cls, url):
        try:
            yield
        except Exception as e:
            logger.info(traceback.format_exc())
            error = FormattedError(
                source=url,
                code=ErrorResponseCodes.bad_thirdparty_request,
                detail=str(e),
            )

            raise ErrorLCResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=[error],
            )

    def get_auth_url(
        self,
        request_token_url: str,
        authorize_url: str,
        callback_url: str,
    ) -> Dict:
        pass

    @abstractmethod
    def list_courses(self) -> List[Course]:
        """
        Pull a list of taught courses
        """

    @abstractmethod
    def list_students_in_course(
        self,
        lms_course_id: str,
        course_sections: Optional[List[str]] = None
    ) -> List[Student]:
        """
        Pull a list of students for the selected course
        """

    @abstractmethod
    def create_grade_for_course(
        self,
        lms_course_id: str,
        grade_details: Dict,
        sections_info=[],
    ) -> Dict:
        """
        Create grade item for given course

        :param lms_course_id
        :param grade_details:
        :param list sections_info: only supported by Canvas
        """

    @abstractmethod
    def create_or_update_grade_for_student(
        self,
        lms_course_id: str,
        lms_student_id: str,
        grade: float,
    ) -> List[Dict]:
        """
        Create grade item with scores for given course
        :rtype: dictionary containing details on created grade item.
                      Example:
                        [
                          {
                            "grade": "1.0",
                            "id": "_2_1",
                            "lineitemId": "_19_1"
                          }
                        ]
        """

    @abstractmethod
    def update_grade_for_course(
        self,
        lms_course_id: str,
        lms_student_id: str,
        grade: float,
    ) -> None:
        """
        Update grade column information on lms side
        """

    @abstractmethod
    def delete_grade_for_course(
        self,
        lms_course_id: str,
        lms_grade_column_id: str,
    ) -> None:
        """
        Delete grade column on lms side
        """

    @abstractmethod
    def list_sections_for_course(
        self,
        lms_course_id: str
    ) -> List[Dict]:
        """
        Pull the list of sections for the selected course
        """

    @abstractmethod
    def get_current_user_info(self) -> LMSUser:
        """
        Get user information about the currently logged in user.
        """
        pass

    @abstractmethod
    def get_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
    ) -> Assignment:
        """
        Get assignment from the LMS, used primarily for confirming
        the existence of an assignment for a grade.

        :param lms_course_id: id of the remote lms course
        :param lms_assignment_id: id of the remote lms assignment
        """

    @abstractmethod
    def post_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        external_assignment_id: str = None
    ):
        """
        Post grade to LMS for an assignment/grade column in a course.

        :param lms_course_id: id of the remote lms course
        :param lms_assignment_id: id of the remote lms assignment
        :param max_grade: maximum grade for the assignment
        :param external_assignment_id: When possible, store external id
            in the LMS. This is the ID generated by you and not the LMS
        """

    @abstractmethod
    def update_assignment(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        external_assignment_id: str = None
    ):
        """
        Post grade to LMS for an assignment/grade column in a course.

        :param lms_course_id: id of the remote lms course
        :param lms_assignment_id: id of the remote lms assignment
        :param max_grade: maximum grade for the assignment
        :param external_assignment_id: When possible, store external id
            in the LMS. This is the ID generated by you and not the LMS
        """

    @abstractmethod
    def post_grades(
        self,
        lms_course_id: str,
        lms_assignment_id: str,
        max_grade: str,
        student_grade_info: List[dict],
        external_assignment_id: str = None
    ):
        """
        Post grade to LMS for an assignment/grade column in a course.

        :param lms_course_id: id of the remote lms course
        :param lms_assignment_id: id of the remote lms assignment
        :param max_grade: maximum grade for the assignment
        :param student_grade_info: payload with grade information varies
                                   between LMSs
        :param external_assignment_id: When possible, store external id
            in the LMS. This is the ID generated by you and not the LMS
        """
