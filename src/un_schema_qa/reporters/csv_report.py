"""Flat CSV report rendering."""

from __future__ import annotations

import csv
import io
import json

from un_schema_qa.models import ValidationResult

_COLUMNS = (
    "schema_version",
    "toolkit_version",
    "project_name",
    "input_fingerprint",
    "run_status",
    "finding_code",
    "severity",
    "validator",
    "message",
    "recommendation",
    "dataset",
    "field",
    "mapping_id",
    "location_path",
    "location_sheet",
    "location_row",
    "location_column",
    "details",
)


def render_csv(result: ValidationResult) -> str:
    """Render one RFC-compatible CSV row per finding."""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for item in result.findings:
        location = item.location
        writer.writerow(
            {
                "schema_version": result.schema_version,
                "toolkit_version": result.toolkit_version,
                "project_name": result.project_name,
                "input_fingerprint": result.input_fingerprint,
                "run_status": result.summary.status.value,
                "finding_code": item.code,
                "severity": item.severity.value,
                "validator": item.validator,
                "message": item.message,
                "recommendation": item.recommendation,
                "dataset": item.dataset or "",
                "field": item.field or "",
                "mapping_id": item.mapping_id or "",
                "location_path": location.path if location else "",
                "location_sheet": location.sheet or "" if location else "",
                "location_row": location.row or "" if location else "",
                "location_column": location.column or "" if location else "",
                "details": json.dumps(
                    item.details,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            }
        )
    return output.getvalue()
