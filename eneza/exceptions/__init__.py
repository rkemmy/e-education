from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _

class InvalidPermissionsException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Invalid Permissions')
    default_code = 'error'

class SimpleValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Invalid data')
    default_code = 'error'

