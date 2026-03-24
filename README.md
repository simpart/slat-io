# slat-io - Python Lambda Utils
A tiny I/O boundary layer for AWS Lambda.

slat-io is a lightweight Python utility library designed to simplify
input validation, error handling, and response formatting for AWS Lambda.

It keeps your Lambda handlers focused on business logic by removing repetitive I/O glue code.

slat-io is intentionally small. It does not try to become a framework.
It helps prevent handler bloat while keeping your code simple.

## Overview

AWS Lambda handlers often become bloated with repetitive code:

 - extracting values from event
 - validating string-based inputs
 - converting them into the required types
 - formatting API responses
 - catching and translating exceptions

slat-io handles these repetitive I/O concerns so your handler logic stays clean and focused.

# Features

## One-line parameter extraction and validation

### Without slat-io

```python
def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}

    page = qs.get("page")
    if page is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "missing page"})
        }

    try:
        page = int(page)
    except ValueError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid page"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"data": {"page": page}})
    }
```

### With slat-io
```python
@api_handler
def lambda_handler(event, context, respond):
    page = param.get_query(event, "page", typ=int, min=1)

    return respond({
        "page": page
    })
```

slat-io removes repetitive event parsing, parameter validation, and response formatting so your Lambda handlers stay small and readable.


### Supports:

 - type casting (str, int, float, bool, list)
 - regex validation
 - value range
 - enum choices
 - explicit null handling (nullable support)
 - automatic error responses
 - explicit API error raising with consistent response formatting

## Automatic error handling

The `@api_handler` decorator wraps your Lambda handler and injects
a `respond()` helper function for building API responses.

```python
@api_handler
def lambda_handler(event, context, respond):
 ...
 return respond({"message": "ok"})
```

### The decorator

  - catches API errors
  - converts unexpected exceptions into HTTP 500 responses
  - injects a ready-to-use response function
  - attaches AWS request IDs automatically


## Unified response format

slat-io ensures that all API responses share a consistent **response body structure**.

### Success:

```json
{
  "data": {...},
  "meta": {
    "request_id": "...",
    "timestamp": "..."
  }
}
```

### Error:

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "detail": "..."
  },
  "meta": {
    "request_id": "...",
    "timestamp": "..."
  }
}
```

slat-io automatically wraps this body into the AWS Lambda proxy integration format.

Example (actual Lambda return value):

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*"
  },
  "body": "{...}"
}
```

The response body is automatically JSON-encoded and enriched with metadata such as the AWS request ID and timestamp.


# Example

```python
import slatio.parameter as param
from slatio.responder import api_handler

@api_handler
def lambda_handler(event, context, respond):
    user_id = param.get_path(event, "userId", required=True, pattern=r"^user_[a-z0-9]{8}$")
    mode = param.get_query(event, "mode", choices=["debug", "release"])

    return respond({
        "message": "slat-io is working!"
    })
```

## Validation examples

```python
# --- query / path / header ---
param.get_query(event, "page", typ=int, min=1)
param.get_query(event, "mode", choices=["debug", "release"])
param.get_query(event, "user_list", typ=list[str], pattern=r"^[A-Z]-[0-9]{3}$", max_len=1)
param.get_path(event, "userId", pattern=r"^user_[a-z0-9]{8}$")
param.get_header(event, "X-Request-Type", required=True)

# --- json (body) ---
param.get_json(event, "profile.age", typ=int, min=0, max=120)
param.get_json(event, "profile.bio", typ=str, nullable=True)
param.get_json(event, "user_list", typ=list[str], pattern=r"^[A-Z]-[0-9]{3}$", max_len=50)

# --- item (post-extraction validation) ---
for user in users:
    user_id = param.get_item(user, "id", pattern=r"^user_[a-z0-9]{8}$")
    age = param.get_item(user, "profile.age", typ=int, min=0, max=120)
```


# Parameter Extraction
slat-io provides utilities for extracting and validating parameters from Lambda events.
The extraction logic is divided into two categories based on the nature of the input source: TEXT-based and JSON-based.


## TEXT-based Parameters (Query, Path, Header)
These utilities extract values from URL query strings, path parameters, and HTTP headers. Since these sources provide data as strings, the functions perform Type Coercion to convert them into your desired Python types.
Functions: get_query, get_path, get_header

| Parameter | Type | Description |
|:--|:--|:--|
| `event` | `Dict[str, Any]` | AWS Lambda event object |
| `key` | `str` | Name of the parameter to extract |
| `typ` | `Type` | Optional type casting (e.g. `int`, `float`, `bool`, `list`) |
| `required` | `bool` | If `True`, raises an error when the value is missing (default:True) |
| `min /max` | `float` | range validation for numeric types. |
| `pattern` | `str` | Regex pattern used for string validation |
| `choices` | `Sequence[Any]` | Restricts the value to a predefined set |
| `scalar_as_list` | bool | If True and typ is list[T], wraps a single string into a list. Default: False. (get_query only) |
| `max_len` | int | List size validation. Maximum number of items allowed in the list. (get_query only) |

## JSON-based Parameters (Body)
These utilities extract values from the JSON request body. They support Dot-notation (e.g., user.profile.id) for deep extraction and provide specific handling for JSON null values.
Functions: get_json, get_item_value

| Parameter | Type | Description |
|:--|:--|:--|
| `event` | `Dict[str, Any]` | AWS Lambda event object |
| `json_path` | str	| Dot-separated path to the value (e.g., settings.theme).|
| `typ` | `Type` | Optional type casting (e.g. `int`, `float`, `bool`, `list`) |
| `nullable` | `bool` | If True, explicitly allows the JSON value to be null. |
| `required` | `bool` | If `True`, raises an error when the value is missing (default:True) |
| `min /max` | `float` | range validation for numeric types. |
| `pattern` | `str` | Regex pattern used for string validation |
| `choices` | `Sequence[Any]` | Restricts the value to a predefined set |
| `scalar_as_list` | bool | If True and typ is list[T], wraps a single string into a list. Default: False. |
| `max_len` | int | List size validation. Maximum number of items allowed in the list. |

## API List

Compatible with API Gateway payload format v1 and v2.

```python
import slatio.parameter as param

# Path parameters
param.get_path(...)

# Query parameters
param.get_query(...)

# Headers
param.get_header(...)

# JSON body
param.get_json(...)

# Values inside extracted JSON items
param.get_item_value(...)
```

# Raising API errors explicitly

In addition to automatic validation errors, you can raise HTTP-style API errors directly from your handler.

```python
from slatio.responder import api_handler, Unauthorized, NotFound, Conflict

@api_handler
def lambda_handler(event, context, respond):
    if not validate_secret(event):
        raise Unauthorized("Invalid Secret", "The provided secret is not valid.")

    item = find_item(...)
    if item is None:
        raise NotFound("Item Not Found", "The requested item does not exist.")

    return respond({"ok": True})
```

## Available API errors include:
- `BadRequest` — **400 Bad Request**
- `Unauthorized` — **401 Unauthorized**
- `Forbidden` — **403 Forbidden**
- `NotFound` — **404 Not Found**
- `Conflict` — **409 Conflict**
- `UnprocessableEntity` — **422 Unprocessable Entity**
- `TooManyRequests` — **429 Too Many Requests**
- `MethodNotAllowed` — **405 Method Not Allowed**
- `UnsupportedMediaType` — **415 Unsupported Media Type**
- `InternalServerError` — **500 Internal Server Error**
- `BadGateway` — **502 Bad Gateway**
- `ServiceUnavailable` — **503 Service Unavailable**
- `GatewayTimeout` — **504 Gateway Timeout**

# Installation

slat-io is currently distributed as source code for direct use in AWS Lambda projects.

## Direct inclusion

Place the slatio/ package at the top level of your Lambda deployment source:

```
your-project/
├── lambda_function.py
└── slatio/
```

# License
MIT
