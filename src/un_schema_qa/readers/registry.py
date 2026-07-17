"""Input reader dispatch."""

from __future__ import annotations

from pathlib import Path

from un_schema_qa.exceptions import InputFormatError

from .base import TabularRows
from .delimited import read_csv_rows
from .structured import read_structured_rows


def read_rows(path: Path | str, *, sheet: str | None = None) -> TabularRows:
    resolved = Path(path).expanduser().resolve()
    suffix = resolved.suffix.casefold()
    if suffix == ".csv":
        if sheet is not None:
            raise InputFormatError("sheet selection is only supported for Excel workbooks")
        return read_csv_rows(resolved)
    if suffix in {".json", ".yaml", ".yml"}:
        if sheet is not None:
            raise InputFormatError("sheet selection is only supported for Excel workbooks")
        return read_structured_rows(resolved)
    if suffix in {".xlsx", ".xlsm"}:
        from .excel import read_xlsx_rows

        return read_xlsx_rows(resolved, sheet=sheet)
    raise InputFormatError(f"unsupported input format {suffix or '<none>'!r}: {resolved}")
