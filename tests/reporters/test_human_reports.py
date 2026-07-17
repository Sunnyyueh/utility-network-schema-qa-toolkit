from un_schema_qa.models import Finding, Severity, ValidationResult
from un_schema_qa.reporters import render_html, render_markdown, write_reports


def result(*findings: Finding) -> ValidationResult:
    return ValidationResult.from_findings(
        project_name="Water <Migration> & QA",
        input_fingerprint="c" * 64,
        validators=("schema", "mapping"),
        findings=findings,
    )


def test_markdown_report_contains_summary_and_grouped_tables() -> None:
    rendered = render_markdown(
        result(
            Finding(
                code="MAP_FIELD_UNKNOWN",
                severity=Severity.ERROR,
                validator="mapping",
                message="Unknown field | material\nSecond line.",
                recommendation="Correct the field.",
                dataset="WaterLine",
            ),
            Finding(
                code="SCHEMA_TYPE_UNSUPPORTED",
                severity=Severity.WARNING,
                validator="schema",
                message="Unsupported type.",
                recommendation="Use a normalized type.",
            ),
        )
    )

    assert "# Utility Network Schema QA Report" in rendered
    assert "**Status:** `fail`" in rendered
    assert "## mapping" in rendered
    assert "## schema" in rendered
    assert "Unknown field \\| material<br>Second line." in rendered
    assert rendered.endswith("\n")


def test_markdown_empty_report_has_explicit_no_findings_state() -> None:
    rendered = render_markdown(result())

    assert "**Status:** `pass`" in rendered
    assert "No findings were reported." in rendered


def test_html_report_is_self_contained_accessible_and_escaped() -> None:
    rendered = render_html(
        result(
            Finding(
                code="HTML_ESCAPE",
                severity=Severity.WARNING,
                validator="mapping",
                message="<script>alert('unsafe')</script>",
                recommendation="Review <all> values.",
            )
        )
    )
    lower = rendered.casefold()

    assert rendered.startswith("<!DOCTYPE html>")
    assert "<header" in lower
    assert "<main" in lower
    assert "<footer" in lower
    assert 'aria-label="validation summary"' in lower
    assert "<style>" in lower
    assert "&lt;script&gt;alert" in rendered
    assert "<script" not in lower
    assert "http://" not in lower
    assert "https://" not in lower


def test_html_empty_report_has_no_findings_panel() -> None:
    rendered = render_html(result())

    assert "No findings were reported" in rendered
    assert 'data-status="pass"' in rendered


def test_write_reports_generates_all_human_and_machine_formats(tmp_path) -> None:
    paths = write_reports(result(), tmp_path)

    assert set(paths) == {"json", "csv", "markdown", "html"}
    assert paths["markdown"].name == "validation-report.md"
    assert paths["html"].read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
