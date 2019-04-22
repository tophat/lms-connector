"""lms_connector URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from lms_connector import views

urlpatterns = [
    path(
        'auth_url',
        views.AuthUrlView.as_view(),
        name='auth_url'
    ),
    path(
        'users/current',
        views.CurrentUserView.as_view(),
        name='current_user',
    ),
    path(
        'courses',
        views.CoursesView.as_view(),
        name='courses',
    ),
    path(
        'courses/<str:lms_course_id>/enrollments',
        views.EnrollmentsView.as_view(),
        name='course_enrollments',
    ),
    path(
        'courses/<str:lms_course_id>'
        '/assignments/<str:lms_assignment_id>',
        views.AssignmentView.as_view(),
        name='assignments',
    ),
    path(
        'courses/<str:lms_course_id>'
        '/assignments/<str:lms_assignment_id>/grades',
        views.GradesView.as_view(),
        name='grades',
    ),
    path(
        '',
        views.DjangoTestEndpoint.as_view(),
        name='django_test',
    ),
]
