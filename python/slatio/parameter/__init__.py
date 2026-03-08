"""
Kusabi Parameter Utility Package

This package provides a robust set of tools for parsing and validating 
incoming event data from AWS Lambda, specifically optimized for 
API Gateway (payload format v1 and v2).

By delegating the repetitive tasks of data extraction, type conversion, 
and pattern matching to this utility, developers can maintain a clean, 
logic-focused codebase while ensuring strict I/O integrity.
"""


from .param import (
    get_query,
    get_path,
    get_header,
    get_json_value
)
from .value_specification import (
    ValueSpecification,
    InputSource
)

# Explicitly define exported symbols for 'from slatio.parameter import *'
__all__ = [
    "get_query",
    "get_path",
    "get_header",
    "get_json_value",
    "ValueSpecification",
    "InputSource",
 ]
