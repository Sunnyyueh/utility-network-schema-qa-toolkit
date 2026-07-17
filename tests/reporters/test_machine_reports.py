import csv
import io
import json
from pathlib import Path

import jsonschema
import pytest

from un_schema_qa.models import (
    Finding,
    Severity,
    SourceLocation,
    ValidationResult,
)
from un_schema_qa.reporters import render_csv, render_json, write_reports

SCHEMA = Path(__file__).parents[2] / "schemas" / "validation-report-v1.schema.json"


def result() -> ValidationResult:
    return ValidationResult.from_findings(
        project_name="Water & Sewer QA",
        input_fingerprint="a" * 64,
        validators=("schema", "mapping"),
        findings=(
            Finding(
                code="MAP_TEST",
                severity=Severity.WARNING,
                validator="mapping",
                message='Value contains a comma, quote " and newline\nfor CSV.',
                recommendation="Review <mapping>.",
                dataset="WaterLine",
                field="material",
                mapping_id="water-main",
                location=SourceLocation(
                    path="inputs/mapping.csv", sheet="Mappings", row=2, column="material"
                ),
                details={"codes": ["DI", "PVC"], "count": 2},
            ),
        ),
    )


def test_json_report_is_deterministic_and_validates_against_schema() -> None:
    first = render_json(result())
    second = render_json(result())
    payload = json.loads(first)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert first == second
    assert first.endswith("\n")
    jsonschema.validate(payload, schema)
    assert payload["summary"]["status"] == "warning"
    assert payload["findings"][0]["details"]["count"] == 2


def test_csv_report_escapes_values_and_encodes_details_as_json() -> None:
    rendered = render_csv(result())
    rows = list(csv.DictReader(io.StringIO(rendered)))

    assert len(rows) == 1
    assert rows[0]["message"].endswith("newline\nfor CSV.")
    assert json.loads(rows[0]["details"]) == {"codes": ["DI", "PVC"], "count": 2}
    assert rows[0]["location_row"] == "2"


def test_csv_report_with_no_findings_still_has_header() -> None:
    empty = ValidationResult.from_findings(
        project_name="empty",
        input_fingerprint="b" * 64,
        validators=("schema",),
        findings=(),
    )

    rows = list(csv.reader(io.StringIO(render_csv(empty))))

    assert len(rows) == 1
    assert rows[0][0:3] == ["schema_version", "toolkit_version", "project_name"]


def test_write_reports_uses_fixed_names_and_replaces_existing_files(
    tmp_path: Path,
) -> None:
    output = tmp_path / "nested" / "reports"
    output.mkdir(parents=True)
    existing = output / "validation-report.json"
    existing.write_text("stale", encoding="utf-8")

    paths = write_reports(result(), output, formats=("json", "csv"))

    assert paths == {
        "json": output.resolve() / "validation-report.json",
        "csv": output.resolve() / "validation-report.csv",
    }
    assert existing.read_text(encoding="utf-8") == render_json(result())
    assert not list(output.glob("*.tmp"))


def test_write_reports_rejects_unknown_or_path_like_formats(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported report format"):
        write_reports(result(), tmp_path, formats=("../json",))
