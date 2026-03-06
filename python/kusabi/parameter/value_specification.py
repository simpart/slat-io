"""
Kusabi Value Specification Logic

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
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Type, Union
from enum import Enum
from ..responder.ClientError import BadRequest

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
    """
    typ: Type

    # numeric constraints
    min: Optional[float] = None
    max: Optional[float] = None

    # string constraint
    pattern: Optional[str] = None

    # enum constraint (works for str/int/bool etc.)
    choices: Optional[Sequence[Any]] = None

    def _check_structure(self, val: Any, *, source: InputSource):
        """
        Performs preliminary type validation based on the input source.
        
        Handles strict checking to prevent 'loose' Python type matching 
        (e.g., ensuring a boolean is not treated as an integer in JSON).
        """ 

        if source is None:
            raise TypeError("source must be provided (InputSource.TEXT or InputSource.JSON)")

        if val is None:
            return

        if self.typ is int:
            if source == InputSource.JSON:
                if not (isinstance(val, int) and not isinstance(val, bool)):
                    raise BadRequest("Invalid Parameter", "value must be int")
            else:
                if isinstance(val, bool): # boolはintのサブクラスなので個別排除
                    raise BadRequest("Invalid Parameter", "value must be int")
                if isinstance(val, int):
                    return
                if isinstance(val, str):
                    if not val.lstrip('-').isdigit():
                        raise BadRequest("Invalid Parameter", "value must be numeric string")
                    return
                raise BadRequest("Invalid Parameter", "value must be int or numeric string")
        elif self.typ is bool:
            if source == InputSource.JSON:
                if not isinstance(val, bool):
                    raise BadRequest("Invalid Parameter", "value must be bool")
            else:
                if isinstance(val, bool):
                    return  # 念のため（通常TEXTでは来ない）
                s = str(val)  # stripしない
                if s not in (_TRUE | _FALSE):
                    raise BadRequest("Invalid Parameter", 'value must be "true" or "false"')
        elif self.typ is list:
            if not isinstance(val, list):
                raise BadRequest("Invalid Parameter", "value must be a list (array)")
#            if source == InputSource.JSON:
#                if not isinstance(val, list):
#                    raise BadRequest("Invalid Type", "value must be a list (array)")
#            else:
#                if not isinstance(val, list):
#                    raise BadRequest("Invalid Type", "value must be a list (array)")
#            # リストの中身の構造チェック（再帰）
#            if self.item_spec:
#                for item in val:
#                    # 中身の「型」を明示的に渡して、自分自身のロジックを再利用
#                    self._check_structure(item, target_typ=self.item_spec.typ, source=source)

        elif self.typ is float:
            if source == InputSource.JSON:
                if not isinstance(val, float):
                    raise BadRequest("Invalid Parameter", "value must be float")
                if not math.isfinite(val):
                    raise BadRequest("Invalid Parameter", "value must be finite float")
            else:
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    if not math.isfinite(float(val)):
                        raise BadRequest("Invalid Parameter", "value must be finite float")
                    return
                try:
                    f = float(val)
                except Exception:
                    raise BadRequest("Invalid Parameter", "value must be float")

                if not math.isfinite(f):
                    raise BadRequest("Invalid Parameter", "value must be finite float")
        elif self.typ is str:
            if not isinstance(val, str):
                raise BadRequest("Invalid Parameter", "value must be string")



    def cast(self, val: Any) -> Any:
        """
        Converts a validated raw value to the target Python type.

        Args:
            val (Any): The value to cast. Assumes _check_structure has passed.

        Returns:
            Any: The casted value.
        """
        if val is None:
            return None

        if self.typ is str:
            return str(val)

        elif self.typ is int:
            # _check_structure で bool 排除済みの前提だが、防御的に残してもOK
            if isinstance(val, bool):
                raise BadRequest(detail="value must be int")
            return int(val)

        elif self.typ is float:
            return float(val)

        elif self.typ is bool:
            if val == _TRUE:
                return True
            elif val == _FALSE:
                return False
            else:
                raise BadRequest("Invalid Parameter", "value must be 'true' or 'false'")
        elif self.typ is list:
            if not isinstance(val, list):
                raise BadRequest("Invalid Parameter", "value must be a list (array)")
            return val

        # generic callable-type conversion (チェック済みなので素直に変換)
        return self.typ(val)  # type: ignore[misc]



    def validate(self, val: Any) -> bool:
        """
        Enforces constraints (min/max, regex pattern, choices) on the value.

        Args:
            val (Any): The casted or raw value to validate.

        Returns:
            bool: True if validation passes.

        Raises:
            BadRequest: If a constraint is violated.
        """

        # choices
        if self.choices is not None and val not in self.choices:
            raise BadRequest("Invalid Parameter", f"must be one of {list(self.choices)}")

        # numeric range
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if self.min is not None and val < self.min:
                raise BadRequest("Invalid Parameter", f"must be greater than or equal to {self.min}")
            if self.max is not None and val > self.max:
                raise BadRequest("Invalid Parameter", f"must be less than or equal to {self.max}")

        # string pattern
        if isinstance(val, str):
            if self.pattern is not None and re.fullmatch(self.pattern, val) is None:
                raise BadRequest("Invalid Parameter", f"must match the format '{self.pattern}'")

        # list item_spec already validated in cast/parse via item_spec.parse()
        return True

    def parse(self, val: Any, *, source: InputSource = InputSource.TEXT) -> tuple[Any, Optional[BadRequest]]:
        """
        The main entry point for value processing: checks structure, casts, and validates.

        Args:
            val (Any): The input value.
            source (InputSource): Where the value originated from. Defaults to TEXT.

        Returns:
            Tuple[Any, Optional[BadRequest]]: A tuple containing (result, error).
                - On success: (CastedValue, None)
                - On failure: (None, BadRequestInstance)
        """
        # --- None check ---
        if val is None:
            return None
        
        if source is None:
            raise TypeError("source must be provided (InputSource.TEXT or InputSource.JSON)")

        try:
            casted = val
            # 型チェック
            if self.typ is not None:
                self._check_structure(val, source=source)
                if source == InputSource.TEXT:
                    # キャスト実施
                    casted = self.cast(val)

            self.validate(casted)

            return casted, None
        except BadRequest as e:
            return None, e
