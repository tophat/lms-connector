from django.conf import settings
from rest_framework.permissions import BasePermission


class ValidateApiKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.META.get('HTTP_API_KEY', None)
        return api_key == settings.API_KEY
