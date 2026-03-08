"""
Kusabi Response Generator

This module defines the standard response format for all API outputs.
It ensures that both success and error responses follow a consistent 
structure, including automatic metadata injection (timestamp, request ID) 
and CORS header management.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional, Dict

def _response(
    body: dict[str, Any],
    status_code: int,
    request_id: str | None = None,
    cors: bool = True,
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:

    meta = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    if meta_extra:
        meta.update(meta_extra)

    body["meta"] = meta

    headers = {
        "Content-Type": "application/json"
    }

    if cors:
        headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        })

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body, ensure_ascii=False),
    }


def api_response(
    data: Any,
    code: int = 200,
    request_id: str | None = None,
    cors: bool = True,
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:

    body = {
        "data": data
    }

    return _response(body, code, request_id, cors, meta_extra)


def err_response(
    error_code: str,
    message: str,
    detail: str | None = None,
    code: int = 400,
    request_id: str | None = None,
    cors: bool = True,
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:

    error = {
        "code": error_code,
        "message": message,
    }

    if detail is not None:
        error["detail"] = detail

    body = {
        "error": error
    }

    return _response(body, code, request_id, cors, meta_extra)


# --- Base Error Class ---
class ApiError(Exception):
    """
    Base exception class for all Kusabi-related API errors.

    Kusabi errors follow a 3-layer information architecture:
    1. error.code (Machine-Readable): 
       A stable, uppercase string (e.g., 'INVALID_INPUT') used by clients 
       to programmatically determine the error type.
    2. error.message (End-User Focused): 
       A human-readable summary intended to be displayed to the end-user.
    3. error.detail (Developer Focused): 
       Context-specific details, such as validation failure reasons, 
       to assist in debugging or providing field-level feedback.
    """
    def __init__(self, status_code, error_code, message, detail=None, cors: bool = True):
        self.status_code 	= status_code
        self.error_code 	= error_code
        self.message 		= message
        self.detail 		= detail
        self.cors           = True
        self.request_id 	= None 		# Injected by @api_handler
        super().__init__(message)

    def response(self, message=None, detail=None):
        """
        Converts the exception into a standardized error response via err_response().
        """
        return err_response(
            error_code=self.error_code,
            message=message or self.message,
            detail=detail or self.detail,
            status_code=self.status_code,
            request_id=self.request_id,
            cors=cors
        )

