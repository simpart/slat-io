"""
Kusabi Responder Package

The core of this package is the `@api_handler` decorator, which automates 
the execution lifecycle by:
1. Orchestrating the handler execution.
2. Intercepting custom exceptions (ClientError/ServerError) and converting 
   them into structured HTTP responses.
3. Injecting the `respond` utility for consistent JSON output.

By delegating the repetitive task of response formatting and status code 
management to this package, developers can ensure a uniform API contract 
across the entire service.
"""

# 1. Core utilities and Decorators
from .responder import ApiError, api_response
from .decorator import api_handler

# Extracted individually for a cleaner developer experience
# Standardized error classes for upstream/internal failures
from .errors import (
    BadRequest, 
    Unauthorized, 
    Forbidden, 
    NotFound, 
    Conflict, 
    UnprocessableEntity, 
    TooManyRequests, 
    MethodNotAllowed, 
    UnsupportedMediaType,
    InternalServerError,
    BadGateway,
    ServiceUnavailable,
    GatewayTimeout
)

# Explicitly define exported symbols for 'from slatio.responder import *'
__all__ = [
    "api_handler",
    "api_response",
    "ApiError",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "UnprocessableEntity",
    "TooManyRequests",
    "MethodNotAllowed",
    "UnsupportedMediaType",
    "InternalServerError",
    "BadGateway",
    "ServiceUnavailable",
    "GatewayTimeout",
]
