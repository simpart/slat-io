# slat-io - Python Lambda Utils
A tiny I/O boundary layer for AWS Lambda.

slat-io is a lightweight Python utility library designed to simplify
input validation, error handling, and response formatting for AWS Lambda.

It eliminates repetitive boilerplate and lets you focus purely on business logic.

slat-io is intentionally small.
It does not try to become a framework.
Its role is to provide one clean layer that helps prevent handler bloat without sacrificing simplicity.

## Overview

AWS Lambda handlers often become bloated with repetitive code:

 - extracting values from event

 - validating string-based inputs

 - converting them into the required types

 - formatting API responses

 - catching and translating exceptions

slat-io delegates these repetitive I/O concerns so you can keep your handler logic clean and intentional.


# Why slat-io ?

Typical AWS Lambda API handlers tend to become cluttered with repetitive code:

  - parsing event objects

  - validating parameters

  - formatting API Gateway responses

  - catching and converting exceptions

  - adding metadata like request IDs

slat-io removes this boilerplate and provides a clean and deterministic I/O layer.



# Features

## One-line parameter validation

```
user_id = param.get_path(event, "userId", required=True, pattern=r"^user_[a-z0-9]{8}$")
```

### Supports:

 - type casting

 - regex validation

 - value range

 - enum choices

 - automatic error responses


## Automatic error handling

```
@api_handler
def lambda_handler(event, context, respond):
```

### The decorator

  - catches API errors

  - converts unexpected exceptions into 500

  - injects a ready-to-use response function

  - attaches AWS request IDs automatically


## Unified response format

All responses follow a consistent structure.

### Success:

```
{
  "data": {...},
  "meta": {
    "request_id": "...",
    "timestamp": "..."
  }
}
```

### Error:

```
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

# Example

```
import kusabi.parameter as param
from kusabi.responder import *

@api_handler
def lambda_handler(event, context, respond):
    user_id = param.get_path(event, "userId", required=True, pattern=r"^user_[a-z0-9]{8}$")
    mode = param.get_query(event, "mode", choices=["debug", "release"])

    return respond({
        "message": "slat-io is working!",
        "extracted": {
            "userId": user_id,
            "mode": mode
        }
    })
```

## Validation examples

```
param.get_query(event, "page", type=int, min=1)
param.get_query(event, "mode", choices=["debug", "release"])
param.get_path(event, "userId", pattern=r"^user_[a-z0-9]{8}$")
param.get_header(event, "X-Request-Type", required=True)
param.get_json_value(event, "profile.age", type=int, min=0, max=120)
```


# Parameter Extraction

slat-io provides utilities for extracting and validating parameters from Lambda events.


## Core APIs

### Path parameters

```
user_id = param.get_path(event, "userId", required=True)
```

### Query parameters

```
page = param.get_query(event, "page", type=int, min=1)
```

### Headers

```
trace_id = param.get_header(event, "X-Trace-Id", required=True)
```

### JSON body

```
email = param.get_json_value(event, "user.email", required=True)
```



# Response Structure

slat-io ensures your API remains professional and predictable.

## Success (2xx)

```
{
  "data": { "userId": "user_12345678", "limit": 50 },
  "meta": {
    "request_id": "c6af9ac6-...",
    "timestamp": "2026-03-06T17:00:00Z"
  }
}
```

## Error (4xx/5xx)

```
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Validation Failed",
    "detail": "parameter 'limit': must be less than or equal to 100"
  },
  "meta": {
    "request_id": "c6af9ac6-...",
    "timestamp": "2026-03-06T17:00:05Z"
  }
}
```


# Installation

slat-io is currently distributed as source code for direct use in AWS Lambda projects.

Direct inclusion

Place the kusabi/ package at the top level of your Lambda deployment source:

```
your-project/
├── lambda_function.py
└── slat-io/
```

# License
MIT
