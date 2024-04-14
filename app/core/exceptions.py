from typing import Any, Dict, Optional

from app.core.config import settings
from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    headers: Optional[Dict[str, Any]] = None

    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=self.headers,
        )


class Exception401(CustomHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    headers = {
        "WWW-Authenticate": f'Bearer realm="{settings.JWT_REALM}"',
    }


class EmailExists(CustomHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Email already exists"


class AscOrDescAllowed(CustomHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Either ASC or DESC is allowed"


class TokenExpired(Exception401):
    detail = "Token expired"


class InvalidCredentials(Exception401):
    detail = "Error validating credentials"


class InvalidEmailOrPassword(Exception401):
    detail = "Incorrect email or password"


class PrivelegesError(CustomHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Not enough privileges"


class DisabledUser(CustomHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Account disabled"


class NotFound(CustomHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Not Found"


class RoleInvalid(CustomHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Role Not Found"


class PageBadRequest(CustomHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Page outside of interval"
