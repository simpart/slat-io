"""
Kusabi Client Error Definitions (4xx)

This module defines a suite of exception classes for client-side errors.
Each class is mapped to a specific HTTP status code and provides a 
consistent machine-readable error code for the client to handle.
"""

from .responder import ApiError

class BadRequest(ApiError):
    """400 Bad Request: General client-side input error."""
    def __init__(self, message: str = "Invalid Request", detail: str = None):
        super().__init__(400, "BAD_REQUEST", message, detail)

class UnAuthorized(ApiError):
    """401 Unauthorized: Authentication is required or has failed."""
    def __init__(self, message: str = "Authentication Failed", detail: str = None):
        super().__init__(401, "UN_AUTHORIZED", message, detail)

class Forbidden(ApiError):
    """403 Forbidden: The client does not have access rights to the content."""
    def __init__(self, message: str = "Access Denied", detail: str = None):
        super().__init__(403, "FORBIDDEN", message, detail)

class NotFound(ApiError):
    """404 Not Found: The server cannot find the requested resource."""
    def __init__(self, message: str = "Resource Not Found", detail: str = None):
        super().__init__(404, "NOT_FOUND", message, detail)

class MethodNotAllowed(ApiError):
    """405 Method Not Allowed: The request method is not supported for the resource."""
    def __init__(self, message: str = "Method Not Allowed", detail: str = None):
        super().__init__(405, "METHOD_NOT_ALLOWED", message, detail)

class Conflict(ApiError):
    """409 Conflict: The request conflicts with the current state of the server."""
    def __init__(self, message: str = "Resource Conflict", detail: str = None):
        super().__init__(409, "CONFLICT", message, detail)

class UnsupportedMediaType(ApiError):
    """415 Unsupported Media Type: The media format of the requested data is not supported."""
    def __init__(self, message: str = "Unsupported Media Type", detail: str = None):
        super().__init__(415, "UNSUPPORTED_MEDIA_TYPE", message, detail)

class UnprocessableEntity(ApiError):
    """422 Unprocessable Entity: The request was well-formed but had semantic errors."""
    def __init__(self, message: str = "Validation Failed", detail: str = None):
        super().__init__(422, "UNPROCESSABLE_ENTITY", message, detail)

class TooManyRequests(ApiError):
    """429 Too Many Requests: The user has sent too many requests in a given amount of time."""
    def __init__(self, message: str = "Rate Limit Exceeded", detail: str = None):
        super().__init__(429, "TOO_MANY_REQUESTS", message, detail)
