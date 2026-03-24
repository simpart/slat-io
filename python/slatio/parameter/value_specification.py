"""
This module defines the schema and validation rules for individual parameters.
It ensures strict type integrity and constraint enforcement, distinguishing 
between raw TEXT inputs (query/path/header) and structured JSON inputs.

Key features:
- Source-aware validation (InputSource.TEXT vs InputSource.JSON).
- Strict type checking (e.g., preventing bool-as-int pitfalls).
- Numeric, string (regex), and choice-based constraint enforcement.
"""

from __future__ import annotations

import re, math
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Type, Union, get_origin, get_args
from enum import Enum
from ..responder.errors import BadRequest

_TRUE = {"true"}
_FALSE = {"false"}


class InputSource(str, Enum):
    """
    Enumeration of input data origins.
    
    TEXT: Raw strings from query parameters, path variables, or headers.
    JSON: Structured data parsed from the JSON body.
    """
    TEXT = "text"   # query/path/header
    JSON = "json"   # json body


@dataclass(frozen=True)
class ValueSpecification:
    """
    Defines the validation and casting schema for a single value.

    Attributes:
        typ (Type): The expected Python type (str, int, bool, float, list).
        min (float, optional): Minimum value for numeric types.
        max (float, optional): Maximum value for numeric types.
        pattern (str, optional): Regex pattern for string validation.
        choices (Sequence[Any], optional): A list of allowed values.
        scalar_as_list (bool): If True and typ is list[T], automatically wraps 
                               a single scalar value into a list if it matches type T.
        max_len (int, optional): Maximum number of items allowed in a list.
    """
    typ: Optional[Type] = None

    # numeric constraints
    min: Optional[float] = None
    max: Optional[float] = None

    # string constraint
    pattern: Optional[str] = None

    # enum constraint (works for str/int/bool etc.)
    choices: Optional[Sequence[Any]] = None

    # list options
    scalar_as_list: bool = False

    # Internal properties for generic list handling
    _item_typ: Optional[Type] = field(init=False, default=None)
    
    # list size constraints (number of items)
    max_len: Optional[int] = None
    
    def __post_init__(self):
        # Extract the item type T if typ is a generic list (e.g., list[int])
        origin = get_origin(self.typ)
        args = get_args(self.typ)
        if origin is list and args:
            # Store the inner type (T) for element-wise validation
            object.__setattr__(self, "_item_typ", args[0])

        # Determine the target type for constraint validation
        # If it's a list[T], we validate against T; otherwise, against the type itself.
        check_typ = self._item_typ or self.typ

        # Validate numeric constraints
        if (self.min is not None or self.max is not None):
            if check_typ not in (int, float):
                raise TypeError("min/max requires typ=int or typ=float")
        
        # Validate string constraints
        if (self.pattern is not None) and not (check_typ is str):
            raise TypeError("pattern requires typ=str")
        
        # Ensure scalar_as_list is only enabled for explicit generic lists (list[T])
        if self.scalar_as_list and (self._item_typ is None):
            raise TypeError("scalar_as_list=True requires explicit list[T] type")

    
    def _check_structure(self, val: Any, *, source: InputSource, item_typ: Optional[Type] = None):
        """
        Performs preliminary structural and type validation based on the input source.
        
        This method ensures the input matches the expected schema (Scalar vs. List).
        If 'typ' is a generic list (list[T]), it recursively validates each element.
        It also enforces strict type matching for JSON vs. flexible matching for TEXT.

        Args:
            val (Any): The raw input value to check.
            source (InputSource): The origin of the data (TEXT or JSON).
            item_typ (Optional[Type]): Internal use for recursion. Represents the 
                element type T when validating a list[T].
        
        Raises:
            BadRequest: If the structure or base type is invalid.
        """
        if source is None:
            raise TypeError("source must be provided (InputSource.TEXT or InputSource.JSON)")
        
        if val is None:
            return
        
        # Handle list[T] structure
        if item_typ is None and self._item_typ is not None:
            if not isinstance(val, list):
                if self.scalar_as_list is False:
                    raise BadRequest(message="Invalid Parameter", detail="value must be a list")
                else:
                    # If scalar_as_list is enabled, validate the scalar value against the item type T
                    self._check_structure(val, source=source, item_typ=self._item_typ)
                    return
            # Recursively validate each element in the list against item type T
            for item in val:
                self._check_structure(item, source=source, item_typ=self._item_typ)
            return

        # Determine the effective type to check (either the item type T or the base type)
        chk_typ = item_typ or self.typ
        if chk_typ is int:
            if source == InputSource.JSON:
                # Strict check: JSON integers must not be booleans
                if not (isinstance(val, int) and not isinstance(val, bool)):
                    raise BadRequest(message="Invalid Parameter", detail="value must be int")
            else:
                # TEXT source: Allow numeric strings but reject booleans
                if isinstance(val, bool):
                    raise BadRequest(message="Invalid Parameter", detail="value must be int")
                if isinstance(val, int):
                    return
                if isinstance(val, str):
                    if not val.lstrip('-').isdigit():
                        raise BadRequest(message="Invalid Parameter", detail="value must be numeric string")
                    return
                raise BadRequest(message="Invalid Parameter", detail="value must be int or numeric string")
        elif chk_typ is bool:
            if source == InputSource.JSON:
                # Strict check: JSON booleans must be actual bool types
                if not isinstance(val, bool):
                    raise BadRequest(message="Invalid Parameter", detail="value must be bool")
            else:
                # TEXT source: Allow "true"/"false" strings or actual bool
                if isinstance(val, bool):
                    return
                s = str(val)  # stripしない
                if s not in (_TRUE | _FALSE):
                    raise BadRequest(message="Invalid Parameter", detail='value must be "true" or "false"')
        elif chk_typ is list:
            if not isinstance(val, list):
                raise BadRequest(message="Invalid Parameter", detail="value must be a list (array)")
        elif chk_typ is float:
            # Strict check: Ensure numeric value and not a boolean
            if source == InputSource.JSON:
                if not ((isinstance(val, int) or isinstance(val, float)) and not isinstance(val, bool)):
                    raise BadRequest(message="Invalid Parameter", detail="value must be float")
                if not math.isfinite(val):
                    raise BadRequest(message="Invalid Parameter", detail="value must be finite float")
            else:
                # TEXT source: Validate if the value is float-convertible and finite
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    if not math.isfinite(float(val)):
                        raise BadRequest(message="Invalid Parameter", detail="value must be finite float")
                    return
                try:
                    f = float(val)
                except Exception:
                    raise BadRequest(message="Invalid Parameter", detail="value must be float")

                if not math.isfinite(f):
                    raise BadRequest(message="Invalid Parameter", detail="value must be finite float")
        elif chk_typ is str:
            if not isinstance(val, str):
                raise BadRequest(message="Invalid Parameter", detail="value must be string")



    def _cast(self, val: Any, *, item_typ: Optional[Type] = None) -> Any:
        """
        Converts a validated raw value into the target Python type.

        This method handles recursive casting for list[T] and promotes scalar 
        values to lists if 'scalar_as_list' is enabled. It assumes that 
        _check_structure has already verified the basic integrity of the input.

        Args:
            val (Any): The value to cast.
            item_typ (Optional[Type]): Internal use for recursion. Represents the 
                target element type T for list[T] members.

        Returns:
            Any: The casted value (e.g., int, bool, list[int], etc.).
        """
        if val is None:
            return None

        # Handle list[T] recursive casting and scalar promotion
        if item_typ is None and self._item_typ is not None:
            if isinstance(val, list):
                # Standard list processing: cast each element to type T
                return [self._cast(item, item_typ=self._item_typ) for item in val]
            else:
                # cast the single value as type T
                return self._cast(val, item_typ=self._item_typ)

        # Determine the effective type for this specific casting step
        chk_typ = item_typ or self.typ

        if chk_typ is str:
            return str(val)

        elif chk_typ is int:
            # Strict int casting: reject booleans even if they are int subclasses
            if isinstance(val, bool):
                raise BadRequest(message="Invalid Parameter", detail="value must be int")
            return int(val)

        elif chk_typ is float:
            return float(val)

        elif chk_typ is bool:
            if isinstance(val, bool):
                return val
            s = str(val).lower()
            if s in _TRUE:
                return True
            if s in _FALSE:
                return False
            raise BadRequest(message="Invalid Parameter", detail='value must be "true" or "false"')
        elif chk_typ is list:
            return val

        # Generic type conversion using the determined target type
        return chk_typ(val)  # type: ignore[misc]



    def _validate(self, val: Any, *, is_item: bool = False) -> None:
        """
        Enforces value-level constraints (min/max, regex pattern, choices).

        If 'typ' is a generic list (list[T]), this method recursively validates 
        each element in the list. Constraints like 'min', 'max', and 'pattern' 
        are applied to individual items rather than the list container itself.

        Args:
            val (Any): The casted value to validate.
            is_item (bool): Internal use for recursion. If True, indicates that 
                the validation is being performed on an individual list element.

        Raises:
            BadRequest: If any constraint (choices, numeric range, or regex) 
                is violated.
        """
        if not is_item:
            # validate the number of items for list
            if isinstance(val, list) and self.max_len is not None and len(val) > self.max_len:
                raise BadRequest(message="Invalid Parameter", detail=f"must have no more than {self.max_len} items")
                
            # If typ=list[T] is specified, validate each element in the list recursively.
            if self._item_typ is not None:
                if isinstance(val, list):
                    for item in val:
                        # Validate each element individually
                        self._validate(item, is_item=True)
                    return

        # Choices constraint (applies to both scalars and list elements)
        if self.choices is not None and val not in self.choices:
            raise BadRequest(message="Invalid Parameter", detail=f"must be one of {list(self.choices)}")

        # Numeric range constraints (min / max)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if self.min is not None and val < self.min:
                raise BadRequest(message="Invalid Parameter", detail=f"must be greater than or equal to {self.min}")
            if self.max is not None and val > self.max:
                raise BadRequest(message="Invalid Parameter", detail=f"must be less than or equal to {self.max}")

        # String pattern constraint (regex)
        if isinstance(val, str):
            if self.pattern is not None and re.fullmatch(self.pattern, val) is None:
                raise BadRequest(message="Invalid Parameter", detail=f"must match the format '{self.pattern}'")



    def parse(self, val: Any, *, source: InputSource = InputSource.TEXT) -> tuple[Any, Optional[BadRequest]]:
        """
        The primary entry point for value processing: checks structure, casts, and validates.

        This method executes the complete validation pipeline:
        1. Structural and type integrity check
        2. type conversion (InputSource.TEXT)
        3. Constraint enforcement

        Args:
            val (Any): The raw input value to be processed.
            source (InputSource): The origin of the value (TEXT or JSON). 
                Defaults to InputSource.TEXT.

        Returns:
            tuple[Any, Optional[BadRequest]]: A tuple containing (CastedValue, None) 
                on success, or (None, BadRequest) on failure.
        """
        if source is None:
            raise TypeError("source must be provided (InputSource.TEXT or InputSource.JSON)")
        
        try:
            casted = val
            
            if val is not None and self.typ is not None:
                # Structural check: Verify if the input matches the expected schema
                self._check_structure(val, source=source)
                if source == InputSource.TEXT:
                    # Convert to Python types and handle list[T] recursion
                    casted = self._cast(val)
                
                # wrapping for scalar_as_list
                if self._item_typ and (not isinstance(casted, list)) and self.scalar_as_list is True:
                    casted = [casted]

            # Constraint validation: min/max, pattern, and choices
            self._validate(casted)
                
            return casted, None
        except BadRequest as e:
            return None, e

