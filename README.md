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

slat-io removes repetitive parsing, validation, and response formatting so your handlers stay small and readable.

### Supports:

 - type casting (str, int, float, bool, list)
 - regex validation
 - value range
 - enum choices
 - automatic error responses


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
param.get_query(event, "page", typ=int, min=1)
param.get_query(event, "mode", choices=["debug", "release"])
param.get_path(event, "userId", pattern=r"^user_[a-z0-9]{8}$")
param.get_header(event, "X-Request-Type", required=True)
param.get_json_value(event, "profile.age", typ=int, min=0, max=120)
```


# Parameter Extraction

slat-io provides utilities for extracting and validating parameters from Lambda events.


## Core APIs

### Parameter Extraction

slat-io provides utilities for extracting and validating values from
different parts of the Lambda event object.

All parameter extraction functions support the following options:

| Parameter | Type | Description |
|:--|:--|:--|
| `event` | `Dict[str, Any]` | AWS Lambda event object |
| `key` | `str` | Name of the parameter to extract |
| `typ` | `Type` | Optional type casting (e.g. `int`, `float`, `bool`, `list`) |
| `required` | `bool` | If `True`, raises an error when the value is missing |
| `min` | `float` | Minimum allowed value for numeric parameters |
| `max` | `float` | Maximum allowed value for numeric parameters |
| `pattern` | `str` | Regex pattern used for string validation |
| `choices` | `Sequence[Any]` | Restricts the value to a predefined set |

### API List

```python
import slatio.parameter as param

# Path parameters
param.get_path(...)

# Query parameters
param.get_query(...)

# Headers
param.get_header(...)

# JSON body
param.get_json_value(...)
```

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
