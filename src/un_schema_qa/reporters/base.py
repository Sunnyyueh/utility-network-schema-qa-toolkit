"""Safe report file orchestration."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from un_schema_qa.models import ValidationResult

_FILENAMES = {
    "json": "validation-report.json",
    "csv": "validation-report.csv",
    "markdown": "validation-report.md",
    "html": "validation-report.html",
}


def write_reports(
    result: ValidationResult,
    output_dir: Path | str | None = None,
    *,
    formats: Sequence[str] = ("json", "csv", "markdown", "html"),
) -> dict[str, Path]:
    """Render selected reports and atomically replace fixed output filenames."""

    requested = tuple(value.casefold() for value in formats)
    if len(set(requested)) != len(requested):
        raise ValueError("report formats cannot be duplicated")
    unknown = [value for value in requested if value not in _FILENAMES]
    if unknown:
        raise ValueError(f"unsupported report format(s): {', '.join(unknown)}")
    directory = Path(output_dir or "reports").expanduser().resolve()
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"report output path is not a directory: {directory}")
    directory.mkdir(parents=True, exist_ok=True)

    renderers = _renderers()
    written: dict[str, Path] = {}
    for report_format in requested:
        renderer = renderers.get(report_format)
        if renderer is None:
            raise ValueError(f"unsupported report format: {report_format}")
        destination = directory / _FILENAMES[report_format]
        _atomic_write(destination, renderer(result))
        written[report_format] = destination
    return written


def _renderers() -> dict[str, Callable[[ValidationResult], str]]:
    from .csv_report import render_csv
    from .html_report import render_html
    from .json_report import render_json
    from .markdown_report import render_markdown

    return {
        "json": render_json,
        "csv": render_csv,
        "markdown": render_markdown,
        "html": render_html,
    }


def _atomic_write(destination: Path, content: str) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
