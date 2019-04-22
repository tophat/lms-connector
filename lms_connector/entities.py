from enum import Enum
from typing import (
    List,
    Optional,
)


class Role(Enum):
    student = 'student'


class Course(dict):
    def __init__(self, course_id: str, title: str):
        super(Course, self).__init__([
            ('course_id', course_id),
            ('title', title),
        ])


class Student(dict):
    def __init__(
        self,
        student_id: str,
        email: str,
        role: Role,
        first_name: str,
        last_name: str,
        user_name: str,
    ):
        super(Student, self).__init__([
            ('student_id', student_id),
            ('email', email),
            ('role', role.value),
            ('first_name', first_name),
            ('last_name', last_name),
            ('user_name', user_name),
        ])


class LMSUser(dict):
    def __init__(
        self,
        lms_user_id: str,
        email: str,
        first_name: str,
        last_name: str
    ):
        super(LMSUser, self).__init__([
            ('lms_user_id', lms_user_id),
            ('email', email),
            ('first_name', first_name),
            ('last_name', last_name),
        ])


class Grade(dict):
    def __init__(
        self,
        lms_student_id,
        grade,
    ):
        super(Grade, self).__init__([
            ('lms_student_id', lms_student_id),
            ('grade', grade),
        ])


class Assignment(dict):
    def __init__(
        self,
        title: str,
        max_grade: str,
        grades: Optional[List[Grade]] = None,
    ):
        assignment_items = [
            ('title', title),
            ('max_grade', max_grade),
        ]

        if grades:
            assignment_items.append(('grades', grades))

        super(Assignment, self).__init__(assignment_items)
