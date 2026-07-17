"""Normalization helpers shared by all input readers."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .exceptions import InputFormatError

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def normalize_header(value: str) -> str:
    """Convert a user-facing column name into a stable logical key."""

    stripped = value.lstrip("\ufeff").strip()
    separated = _CAMEL_BOUNDARY.sub("_", stripped).casefold()
    return _NON_ALPHANUMERIC.sub("_", separated).strip("_")


def resolve_columns(
    headers: Sequence[str], logical_schema: Mapping[str, set[str]]
) -> dict[str, str]:
    """Map logical column names to original input headers."""

    aliases = {
        logical: {normalize_header(logical), *(normalize_header(alias) for alias in choices)}
        for logical, choices in logical_schema.items()
    }
    resolved: dict[str, str] = {}
    for header in headers:
        normalized = normalize_header(header)
        for logical, choices in aliases.items():
            if normalized not in choices:
                continue
            if logical in resolved:
                raise InputFormatError(
                    f"multiple columns map to {logical!r}: {resolved[logical]!r} and {header!r}"
                )
            resolved[logical] = header
    return resolved


def parse_bool(value: Any) -> bool | None:
    """Parse common spreadsheet and configuration booleans."""

    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    if value in (1, "1"):
        return True
    if value in (0, "0"):
        return False
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "y", "on"}:
            return True
        if normalized in {"false", "no", "n", "off"}:
            return False
    raise InputFormatError(f"expected boolean value, got {value!r}")


def parse_int(value: Any) -> int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise InputFormatError(f"expected integer value, got {value!r}")
    try:
        converted = int(value)
    except (TypeError, ValueError) as error:
        raise InputFormatError(f"expected integer value, got {value!r}") from error
    if isinstance(value, float) and not value.is_integer():
        raise InputFormatError(f"expected integer value, got {value!r}")
    if isinstance(value, str) and str(converted) != value.strip().lstrip("+"):
        raise InputFormatError(f"expected integer value, got {value!r}")
    return converted


def parse_float(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise InputFormatError(f"expected numeric value, got {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise InputFormatError(f"expected numeric value, got {value!r}") from error


def parse_list(value: Any) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in re.split(r"[,;]", value) if item.strip())
    if isinstance(value, Iterable) and not isinstance(value, (bytes, Mapping)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    raise InputFormatError(f"expected list value, got {value!r}")


_DATA_TYPE_ALIASES = {
    "string": "text",
    "text": "text",
    "esri_field_type_string": "text",
    "small_integer": "small_integer",
    "short": "small_integer",
    "esri_field_type_small_integer": "small_integer",
    "integer": "integer",
    "long": "integer",
    "long_integer": "integer",
    "esri_field_type_integer": "integer",
    "single": "float",
    "float": "float",
    "esri_field_type_single": "float",
    "double": "double",
    "esri_field_type_double": "double",
    "date": "date",
    "datetime": "date",
    "esri_field_type_date": "date",
    "guid": "guid",
    "globalid": "guid",
    "global_id": "guid",
    "oid": "oid",
    "objectid": "oid",
    "object_id": "oid",
    "blob": "blob",
    "geometry": "geometry",
}


def normalize_data_type(value: str) -> str:
    key = normalize_header(value)
    return _DATA_TYPE_ALIASES.get(key, key)


_GEOMETRY_ALIASES = {
    "line": "polyline",
    "linestring": "polyline",
    "polyline": "polyline",
    "esri_geometry_polyline": "polyline",
    "point": "point",
    "esri_geometry_point": "point",
    "polygon": "polygon",
    "esri_geometry_polygon": "polygon",
    "table": "table",
    "none": "table",
}


def normalize_geometry_type(value: str) -> str:
    key = normalize_header(value)
    return _GEOMETRY_ALIASES.get(key, key)
