"""
Kusabi API Error Taxonomy (4xx & 5xx)

This module provides a unified suite of exception classes for both client-side 
and server-side failures. Each class is mapped to a specific HTTP status code, 
ensuring that all API failures—from semantic validation errors to catastrophic 
crashes—are returned as structured, machine-readable JSON rather than 
raw stack traces.

Structure:
- Client Errors (4xx): Represent request-level issues with consistent error codes 
  for frontend handling.
- Server Errors (5xx): Act as the final safety net for unhandled exceptions or 
  upstream service unavailability.
"""
from .responder import ApiError

class BadRequest(ApiError):
    """400 Bad Request: General client-side input error."""
    def __init__(self, message: str = "Invalid Request", detail: str = None):
        super().__init__(400, "BAD_REQUEST", message, detail)

class Unauthorized(ApiError):
    """401 Unauthorized: Authentication is required or has failed."""
    def __init__(self, message: str = "Authentication Failed", detail: str = None):
        super().__init__(401, "UNAUTHORIZED", message, detail)

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

class InternalServerError(ApiError):
    """500 Internal Server Error: A generic error message when an unexpected condition was encountered."""
    def __init__(self, message: str = "Internal Server Error", detail: str = None):
        super().__init__(500, "INTERNAL_SERVER_ERROR", message, detail)

class BadGateway(ApiError):
    """502 Bad Gateway: The server received an invalid response from an upstream server."""
    def __init__(self, message: str = "Bad Gateway", detail: str = None):
        super().__init__(502, "BAD_GATEWAY", message, detail)

class ServiceUnavailable(ApiError):
    """503 Service Unavailable: The server is not ready to handle the request (e.g., maintenance)."""
    def __init__(self, message: str = "Service Unavailable", detail: str = None):
        super().__init__(503, "SERVICE_UNAVAILABLE", message, detail)

class GatewayTimeout(ApiError):
    """504 Gateway Timeout: The server acted as a gateway and timed out waiting for a response."""
    def __init__(self, message: str = "Gateway Timeout", detail: str = None):
        super().__init__(504, "GATEWAY_TIMEOUT", message, detail)

