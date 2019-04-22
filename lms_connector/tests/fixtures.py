# In tests you have to prefix headers with http_ manually
# https://stackoverflow.com/a/27366078/10015893
oauth_creds_dict = {
    'HTTP_LMS_CLIENT_KEY': 'aaaaaaaaa4',
    'HTTP_LMS_CLIENT_SECRET': 'jjjjjjj1',
    'HTTP_LMS_OAUTH_TOKEN': 'ssssssss-',
    'HTTP_LMS_OAUTH_SECRET': 'aaaaab',
}


def get_mocked_headers(lms_base_url):
    mocked_headers = {
        'HTTP_LMS_BASE_URL': lms_base_url,
        'HTTP_LMS_TYPE': 'sakai',
    }
    mocked_headers.update(oauth_creds_dict)
    return mocked_headers


current_user_response = {
    'createdDate': 1536238458000,
    'displayId': 'someprof',
    'displayName': 'Ricky Bobby',
    'eid': 'someprof',
    'email': 'profsicle@tophat.com',
    'firstName': 'Ricky',
    'id': '8422855b-e71c-42fe-a431-d0d5d47c3887',
    'lastModified': 1544664162000,
    'lastName': 'Bobby',
    'modifiedDate': 1544664162000,
    'owner': '/user/admin',
    'password': None,
    'props': None,
    'reference': '/user/8422855b-e71c-42fe-a431-d0d5d47c3887',
    'sortName': 'Bobby, Ricky',
    'type': 'maintain',
    'url': 'http://localhost:3462/access/user8422855b-d0d5d47c3887',
    'entityReference': '/user/8422855b-e71c-42fe-a431-d0d5d47c3887',
    'entityURL': 'http://localhost:3462/direct/user/8422855b-d0d5d47c3887',
    'entityId': '8422855b-e71c-42fe-a431-d0d5d47c3887',
    'entityTitle': 'Ricky Bobby'
}

sakai_get_assignment_response = {
    "id": 3,
    "idStr": "3",
    "failed": False,
    "deleted": False,
    "dueDate": 1537207495000,
    "eid": None,
    "failure": None,
    "gradebookId": "067888b9-e611-4189-a185-8648d10c6d65",
    "includedInCourseGrade": True,
    "name": "giname",
    "pointsPossible": 111,
    "released": True,
    "scoreErrors": None,
    "scores": [
        {
            "comment": None,
            "error": None,
            "grade": "33",
            "graderUserId": None,
            "id": "3:3ae78166-4072-404b-bdc1-40e05b2a5221",
            "itemId": "3",
            "recorded": 1547078120505,
            "userId": "3ae78166-4072-404b-bdc1-40e05b2a5221",
            "username": "studentbuffalosuny"
        }
    ],
    "type": "GB_REST",
    "entityReference": "/grades/3",
    "entityURL": "http://localhost:3462/direct/grades/3",
    "entityId": "3",
    "entityTitle": "gradeitem"
}

sakai_post_grade_data = {
    "max_grade": "100",
    "external_assignment_id": "sssssssssssdddddd",
    "grades": [{
        "lms_student_id": "08f72871-4f03-4d76-8de6-eb35aba9f8f4",
        "grade": "72"
    }]
}

sakai_post_assignment_data = {
    "max_grade": "100",
    "external_assignment_id": "sssssssssssdddddd",
    "grades": [],
}

sakai_post_grade_response = {
    'deleted': False,
    'dueDate': None,
    'eid': sakai_post_grade_data['external_assignment_id'],
    'entityId': '82',
    'entityReference': '/grades/82',
    'entityTitle': 'gradeitem',
    'entityURL': 'http://localhost:3462/direct/grades/82',
    'failed': False,
    'failure': None,
    'gradebookId': '067888b9-e611-4189-a185-8648d10c6d65',
    'id': 82,
    'idStr': '82',
    'includedInCourseGrade': False,
    'name': 'thinsusssslateONEMOREE',
    'pointsPossible': float(sakai_post_grade_data['max_grade']),
    'released': False,
    'scoreErrors': None,
    'scores': [{
        'comment': None,
        'error': None,
        'grade': sakai_post_grade_data['grades'][0]['grade'],
        'graderUserId': None,
        'id': '82:08f72871-4f03-4d76-8de6-eb35aba9f8f4',
        'itemId': '82',
        'recorded': None,
        'userId': sakai_post_grade_data['grades'][0]['lms_student_id'],
        'username': 'sakai_th_student4',
    }],
    'type': 'internal'
}

# These two are the same endpoint for Sakai
sakai_post_assignment_response = sakai_post_grade_response

sample_html_error_message = (
    "Cannot execute custom action (students): Illegal arguments: "
    "No course found with id (kjhsd) (rethrown)"
)

sample_html_error_message_page = (
    f'<html><p>Status Report</p><p><b>Message</b> {sample_html_error_message}'
    '</p><p><b>Description</b> The server cannot or will not '
    'process the request due to something that is perceived to be a '
    'client error (e.g., malformed request syntax, invalid request message '
    'framing, or deceptive request routing).</p></html>'
)
