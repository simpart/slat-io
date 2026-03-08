"""
Kusabi Parameter Extraction Logic

This module provides high-level utilities for extracting and validating
parameters from AWS Lambda event objects. It is fully compatible with
API Gateway Payload Format v1.0 and v2.0.

By delegating the complexities of input parsing (including Base64 decoding,
JSON body caching, and case-insensitive header normalization) to this
module, developers can ensure strict I/O integrity while keeping the
main handler focused on business logic.
"""

from __future__ import annotations

import base64, json
from typing import Any, Dict, List, Optional, Union, Sequence, Type

from ..responder.errors import BadRequest
from .value_specification import ValueSpecification, InputSource


def _headers_dict(event: Dict[str, Any]) -> Dict[str, str]:
    raw = event.get("headers")
    if not isinstance(raw, dict):
        return {}

    normalized: Dict[str, str] = {}

    for k, v in raw.items():
        key = str(k).lower()
        val = "" if v is None else str(v)
        normalized[key] = val

    return normalized



def _maybe_decode_body(event: Dict[str, Any]) -> Optional[str]:
    body = event.get("body")
    if body is None:
        return None
    if not isinstance(body, str):
        # API Gateway body is usually str; if not, coerce to str
        body = str(body)

    if event.get("isBase64Encoded") is True:
        try:
            raw = base64.b64decode(body)
            return raw.decode("utf-8")
        except Exception:
            raise BadRequest("Invalid Parameter", "body is base64 encoded but could not be decoded")
    return body



def get_query(
    event: Dict[str, Any],
    key: str,
    *,
    type: Type = None,
    required: bool = False,
    min: Optional[float] = None,
    max: Optional[float] = None,
    pattern: Optional[str] = None,
    choices: Optional[Sequence[Any]] = None,
) -> Optional[Any]:
    """
    Extracts and validates a query parameter from the Lambda event.

    This function abstracts the differences between API Gateway Payload Format v1.0 
    (multiValueQueryStringParameters) and v2.0 (queryStringParameters).

    Args:
        event (Dict[str, Any]): The AWS Lambda event object.
        key (str): The name of the query parameter to extract.
        typ (Type, optional): The expected Python type to cast the value. Defaults to None.
        required (bool, optional): If True, raises BadRequest if the key is missing. Defaults to False.
        min (float, optional): Minimum value for numeric validation. Defaults to None.
        max (float, optional): Maximum value for numeric validation. Defaults to None.
        pattern (str, optional): Regex pattern for string validation. Defaults to None.
        choices (Sequence[Any], optional): A list of allowed values. Defaults to None.

    Returns:
        Union[None, str, List[str]]: The validated value. 
            - Returns a `str` if a single value is found.
            - Returns a `List[str]` if multiple values are detected.
            - Performs "Smart Coercion": 
                - Automatically converts single-element lists to a scalar string.
                - Splits comma-separated strings into a list for convenience.

    Raises:
        BadRequest: If the parameter is missing (when required) or fails validation.
    """
    spec = ValueSpecification(
                typ=typ,
                min=min,
                max=max,
                pattern=pattern,
                choices=choices,
            )
    
    # Support for both v1 (multiValueQueryStringParameters) and v2 (queryStringParameters)
    multi_params = event.get("multiValueQueryStringParameters") or {}
    single_params = event.get("queryStringParameters") or {}

    raw_val = None

    # 1. Check multiValueQueryStringParameters first (v1 style)
    if key in multi_params:
        vals = multi_params[key]
        if len(vals) == 1:
            # Smart Coercion: Convert single-element list to a scalar value for convenience
            raw_val = vals[0]
        else:
            raw_val = vals

    # 2. Fallback to queryStringParameters (v2 style or single-value fallback)
    elif key in single_params:
        val = single_params[key]
        if "," in val:
            # Smart Coercion: Automatically split comma-separated strings into a list
            raw_val = [v.strip() for v in val.split(",")]
        else:
            raw_val = val

    # --- required check（getter 側） ---
    if raw_val is None:
        if required:
            raise BadRequest(message="Missing Parameter", detail=f"{key} query parameter is required")
        return None

    result, error = spec.parse(raw_val)
    if error:
        error.detail = f"parameter '{key}': {error.detail}"
        raise error

    return result


def get_path(
    event: Dict[str, Any],
    key: str,
    *,
    typ: Type = None,
    required: bool = False,
    min: Optional[float] = None,
    max: Optional[float] = None,
    pattern: Optional[str] = None,
    choices: Optional[Sequence[Any]] = None,
) -> Optional[Any]:
    """
    Extracts and validates a path parameter from the Lambda event.

    This function handles path parameters for both API Gateway Payload Format v1.0 
    and v2.0, providing a unified way to access route-defined variables.

    Args:
        event (Dict[str, Any]): The AWS Lambda event object.
        key (str): The name of the path parameter to extract (as defined in the API route).
        typ (Type, optional): The expected Python type to cast the value. Defaults to None.
        required (bool, optional): If True, raises BadRequest if the key is missing from pathParameters. 
            Defaults to False.
        min (float, optional): Minimum value for numeric validation. Defaults to None.
        max (float, optional): Maximum value for numeric validation. Defaults to None.
        pattern (str, optional): Regex pattern for string validation. Defaults to None.
        choices (Sequence[Any], optional): A list of allowed values. Defaults to None.

    Returns:
        Optional[Any]: The validated and casted value. Returns None if the parameter 
            is missing and `required` is False.

    Raises:
        BadRequest: If the parameter is missing (when required) or fails validation 
            against the provided specifications.
    """

    spec = ValueSpecification(
                typ=typ,
                min=min,
                max=max,
                pattern=pattern,
                choices=choices,
            )
    
    # Both v1 and v2 use "pathParameters" for route variables.
    pp = event.get("pathParameters")
    value = None
    if isinstance(pp, dict):
        value = pp.get(key)

    # --- Validation: Required Check ---
    if value is None:
        if required:
            raise BadRequest(message="Missing Parameter", detail=f"{key} path parameter is required")
        return None
    
    # --- Validation: Specification Match ---
    result, error = spec.parse(value)
    if error:
        error.detail = f"'{key}': {error.detail}"
        raise error

    return result

def get_header(
    event: Dict[str, Any],
    key: str,
    *,
    typ: Type = None,
    required: bool = False,
    min: Optional[float] = None,
    max: Optional[float] = None,
    pattern: Optional[str] = None,
    choices: Optional[Sequence[Any]] = None,
) -> Any:
    """
    Extracts and validates an HTTP header from the Lambda event.

    This function provides case-insensitive header access by normalizing 
    all header keys to lowercase, ensuring compatibility across different 
    HTTP protocols and client implementations.

    Args:
        event (Dict[str, Any]): The AWS Lambda event object.
        key (str): The name of the header to extract. Case-insensitive.
        typ (Type, optional): The expected Python type to cast the value. Defaults to None.
        required (bool, optional): If True, raises BadRequest if the header is missing. 
            Defaults to False.
        min (float, optional): Minimum value for numeric validation. Defaults to None.
        max (float, optional): Maximum value for numeric validation. Defaults to None.
        pattern (str, optional): Regex pattern for string validation. Defaults to None.
        choices (Sequence[Any], optional): A list of allowed values. Defaults to None.

    Returns:
        Any: The validated and casted value. Returns None if the header is 
            missing and `required` is False.

    Raises:
        BadRequest: If the header is missing (when required) or fails validation.
    """

    spec = ValueSpecification(
                typ=typ,
                min=min,
                max=max,
                pattern=pattern,
                choices=choices,
            )
    
    # Normalize headers to ensure case-insensitive lookup
    headers = _headers_dict(event)
    if not headers:
        if required:
            raise BadRequest(message="Missing Parameter", detail=f"{key} header is required")
        return None
    
    # HTTP header keys are case-insensitive; looking up using lowercase key
    val = headers.get(key.lower())
    if val is None:
        if required:
            raise BadRequest(message="Missing Parameter", detail=f"{key} header is required")
        return None

    # --- Validation: Specification Match ---
    result, error = spec.parse(val)
    if error:
        error.detail = f"parameter '{key}': {error.detail}"
        raise error

    return result



_CACHE_KEY = "_slat_io"          # event内のキャッシュ領域
_BODY_CACHE_KEY = "json_body"     # パース済みbodyのキー

def _get_cached_json_body(event: Dict[str, Any], *, required: bool) -> Dict[str, Any]:
    cache = event.setdefault(_CACHE_KEY, {})
    if _BODY_CACHE_KEY in cache:
        return cache[_BODY_CACHE_KEY]

    body = _maybe_decode_body(event)
    if body is None or body == "":
        if required:
            raise BadRequest(message="Missing Parameter", detail="body is required")
        parsed: Dict[str, Any] = {}
        cache[_BODY_CACHE_KEY] = parsed
        return parsed

    try:
        data = json.loads(body)
    except Exception:
        raise BadRequest(message="Invalid Parameter", detail="body must be valid json")

    if not isinstance(data, dict):
        raise BadRequest(message="Invalid Parameter", detail="body value must be a json object")

    cache[_BODY_CACHE_KEY] = data
    return data


def _dig(payload: Any, path: str) -> Any:
    cur = payload
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def get_json_value(
    event: Dict[str, Any],
    json_path: Optional[str] = None,
    *,
    typ: Type = None,
    required: bool = False,
    min: Optional[float] = None,
    max: Optional[float] = None,
    pattern: Optional[str] = None,
    choices: Optional[Sequence[Any]] = None,
) -> Optional[Any]:
    """
    Extracts and validates a value from the JSON body using dot-notation path.

    This function performs memoized parsing; the JSON body is parsed and cached 
    within the `event` object on the first call to avoid redundant processing. 
    It supports Base64-encoded bodies automatically.

    Args:
        event (Dict[str, Any]): The AWS Lambda event object.
        json_path (str, optional): The dot-separated path to the desired value 
            (e.g., "user.profile.id"). If None or empty, returns the entire 
            parsed JSON body as a dict. Defaults to None.
        typ (Type, optional): The expected Python type to cast the value. Defaults to None.
        required (bool, optional): If True, raises BadRequest if the JSON body 
            is missing or the specified path does not exist. Defaults to False.
        min (float, optional): Minimum value for numeric validation. Defaults to None.
        max (float, optional): Maximum value for numeric validation. Defaults to None.
        pattern (str, optional): Regex pattern for string validation. Defaults to None.
        choices (Sequence[Any], optional): A list of allowed values. Defaults to None.

    Returns:
        Any: The validated and casted value. Returns None if the value is 
            missing and `required` is False.

    Raises:
        BadRequest: If the body is invalid JSON, the required path is missing, 
            or the value fails validation.
    """

    spec = ValueSpecification(
                typ=typ,
                min=min,
                max=max,
                pattern=pattern,
                choices=choices,
            )
    
    # Retrieve the body from cache, or parse it if this is the first call.
    payload = _get_cached_json_body(event, required=required)

    if json_path is None or json_path == "":
        val = payload
    else:
        # Traverse the dict using dot-notation
        val = _dig(payload, json_path)

    if val is None:
        if required:
            raise BadRequest(message="Missing Parameter", detail=f"{json_path} is required")
        return None

    # Note: Using json_path for the error message instead of undefined 'key'
    result, error = spec.parse(val, source=InputSource.JSON)
    if error:
        error.detail = f"parameter '{json_path}': {error.detail}"
        raise error

    return result
