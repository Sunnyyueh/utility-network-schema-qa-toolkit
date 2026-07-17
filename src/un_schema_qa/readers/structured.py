"""JSON and YAML tabular input readers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from un_schema_qa.exceptions import InputFormatError
from un_schema_qa.models import SourceLocation

from .base import TabularRows


def read_structured_rows(path: Path) -> TabularRows:
    resolved = path.expanduser().resolve()
    try:
        text = resolved.read_text(encoding="utf-8-sig")
        if not text.strip():
            raise InputFormatError(f"empty structured input: {resolved}")
        if resolved.suffix.casefold() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text)
    except InputFormatError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise InputFormatError(f"cannot parse structured input {resolved}: {error}") from error

    rows = _coerce_rows(payload, resolved)
    headers = _collect_headers(rows)
    locations = tuple(
        SourceLocation(path=str(resolved), row=index) for index in range(1, len(rows) + 1)
    )
    return TabularRows(headers=headers, rows=rows, locations=locations)


def _coerce_rows(payload: Any, path: Path) -> tuple[dict[str, Any], ...]:
    if isinstance(payload, Mapping) and "rows" in payload:
        payload = payload["rows"]
    elif isinstance(payload, Mapping):
        keyed_rows: list[dict[str, Any]] = []
        for identifier, value in payload.items():
            if not isinstance(value, Mapping):
                raise InputFormatError(f"structured row {identifier!r} is not an object in {path}")
            row = {str(key): item for key, item in value.items()}
            row.setdefault("identifier", str(identifier))
            keyed_rows.append(row)
        payload = keyed_rows

    if not isinstance(payload, list) or not payload:
        raise InputFormatError(f"empty structured input: {path}")

    rows: list[dict[str, Any]] = []
    for index, value in enumerate(payload, start=1):
        if not isinstance(value, Mapping):
            raise InputFormatError(f"structured row {index} is not an object in {path}")
        rows.append({str(key): item for key, item in value.items()})
    return tuple(rows)


def _collect_headers(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    headers: dict[str, None] = {}
    for row in rows:
        for key in row:
            headers.setdefault(key, None)
    return tuple(headers)
