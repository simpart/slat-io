"""
Kusabi Server Error Definitions (5xx)

This module defines exception classes for server-side failures. 
These are typically used to represent unhandled exceptions or 
upstream service unavailability, ensuring that even catastrophic 
failures are returned as structured JSON rather than raw stack traces.
"""

from .responder import ApiError

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
