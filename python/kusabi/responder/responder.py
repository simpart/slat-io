"""
Kusabi Response Generator

This module defines the standard response format for all API outputs.
It ensures that both success and error responses follow a consistent 
structure, including automatic metadata injection (timestamp, request ID) 
and CORS header management.
"""

import json
from datetime import datetime, timezone

# --- Standard Success Response ---
def api_response(body_content, code=200, request_id=None, cors: bool=True):
    """
    Generates a standardized API Gateway response.

    Success responses follow the structure:
    {
        "data": { ... },
        "meta": { "request_id": "...", "timestamp": "..." }
    }

    Args:
        body_content (Any): The main payload to return under the "data" key.
        code (int, optional): HTTP status code. Defaults to 200.
        request_id (str, optional): The unique AWS request ID for traceability.

    Returns:
        Dict[str, Any]: A dictionary formatted for API Gateway proxy integration.
    """
    
    # Structure the response with "data" and "meta" keys
    content = {
        "data": body_content,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    }

    # Build Headers
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
        "statusCode": 	code,
        "headers": 		headers,
        "body": 		json.dumps(content, ensure_ascii=False)
    }


# --- 2. Dedicated Error Response ---
def err_response(
    status_code: int, 
    error_code: str, 
    message: str, 
    detail: Optional[str] = None, 
    request_id: Optional[str] = None,
    cors: bool = True
) -> Dict[str, Any]:
    """
    Generates an error response directly without raising an exception.
    
    Error Structure:
    {
        "error": {
            "code": "...",
            "message": "...",
            "detail": "..."
        },
        "meta": { "request_id": "...", "timestamp": "..." }
    }
    
    Args:
        status_code (int): HTTP status code (e.g., 400, 404, 500).
        error_code (str): Internal application error code.
        message (str): High-level error message.
        detail (str, optional): Detailed error information for debugging.
        request_id (str, optional): AWS Request ID.
        cors (bool, optional): Enable/disable CORS headers. Defaults to True.
    """
    body = {
        "error": {
            "code": error_code,
            "message": message,
            "detail": detail
        }
    }
    return api_response(body, code=status_code, request_id=request_id, cors=cors)


# --- Base Error Class ---
class ApiError(Exception):
    """
    Base exception class for all Kusabi-related API errors.
    """
    def __init__(self, status_code, error_code, message, detail=None):
        self.status_code 	= status_code
        self.error_code 	= error_code
        self.message 		= message
        self.detail 		= detail
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

