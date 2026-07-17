"""Delimited-text input reader."""

from __future__ import annotations

import csv
from pathlib import Path

from un_schema_qa.exceptions import InputFormatError
from un_schema_qa.models import SourceLocation

from .base import TabularRows


def read_csv_rows(path: Path) -> TabularRows:
    resolved = path.expanduser().resolve()
    try:
        with resolved.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise InputFormatError(f"empty CSV input: {resolved}")
            headers = tuple(name.strip() for name in reader.fieldnames if name is not None)
            rows: list[dict[str, object]] = []
            locations: list[SourceLocation] = []
            for row_number, row in enumerate(reader, start=2):
                normalized = {
                    str(key).strip(): value for key, value in row.items() if key is not None
                }
                if not any(value not in (None, "") for value in normalized.values()):
                    continue
                rows.append(normalized)
                locations.append(SourceLocation(path=str(resolved), row=row_number))
    except InputFormatError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise InputFormatError(f"cannot parse CSV input {resolved}: {error}") from error
    if not rows:
        raise InputFormatError(f"empty CSV input: {resolved}")
    return TabularRows(headers=headers, rows=tuple(rows), locations=tuple(locations))
