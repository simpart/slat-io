"""
Kusabi API Handler Decorator (Auto-Pilot Edition)

This module provides the @api_handler decorator, designed to eliminate 
repetitive I/O and error handling patterns in AWS Lambda. 

It acts as a comprehensive "safety net" that:
1. Orchestrates the handler lifecycle.
2. Injects a pre-configured 'respond' utility with the AWS Request ID.
3. Automatically intercepts and formats both expected (ApiError) 
   and unexpected (Exception) failures into a uniform JSON response.
"""

import functools
import traceback
from typing import Any, Callable, Dict
from .responder import api_response
from .errors import ApiError, InternalServerError

def api_handler(func: Callable) -> Callable:
    """
    Wraps the Lambda handler to provide an 'autopilot' execution environment.

    By using this decorator, the handler is shielded from raw exception 
    management and manual response construction.

    Args:
        func: The Lambda handler function (expects: event, context, respond).

    Returns:
        Callable: The shielded handler.
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs):
        # Extract the source of truth for traceability
        req_id = getattr(context, "aws_request_id", None)
        
        # Pre-configured success response utility injected as the 3rd argument
        def respond(body: Any, code: int = 200):
            return api_response(body, code=code, request_id=req_id)
        
        try:
            # Execute core business logic
            return func(event, context, respond, *args, **kwargs)

        except ApiError as e:
            # Safety Net 1: Intercept known API errors
            # Ensure the request_id is attached for the response meta-data
            if not getattr(e, 'request_id', None):
                e.request_id = req_id
            return e.response()            

        except Exception as e:
            # Safety Net 2: The "Final Fortress" against unhandled exceptions.
            # Prevents 502 Bad Gateway by returning a structured 500 Internal Server Error.
            print(f"[ERROR] Unhandled Exception: {str(e)}")
            traceback.print_exc()

            err = InternalServerError(message="An unexpected error occurred.")
            err.request_id = req_id
            # You might want to log the traceback here for internal monitoring
            # traceback.print_exc() 
            return err.response()            

    return wrapper
