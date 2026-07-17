from un_schema_qa.models import (
    Finding,
    RunStatus,
    Severity,
    SourceLocation,
    ValidationResult,
    ValidationSummary,
    deduplicate_findings,
    sort_findings,
)


def finding(code: str, severity: Severity, *, row: int = 1) -> Finding:
    return Finding(
        code=code,
        severity=severity,
        validator="mapping",
        message=f"Message for {code}",
        recommendation="Review the mapping.",
        dataset="WaterLine",
        field="material",
        mapping_id="water-main",
        location=SourceLocation(path="mapping.csv", row=row, column="target_field"),
        details={"expected": "Text", "actual": "Integer"},
    )


def test_severity_has_explicit_order() -> None:
    assert Severity.INFO.rank < Severity.WARNING.rank < Severity.ERROR.rank


def test_findings_have_stable_identity_and_sort_order() -> None:
    warning = finding("MAP_WARNING", Severity.WARNING, row=5)
    error = finding("MAP_ERROR", Severity.ERROR, row=9)
    duplicate = warning.model_copy(update={"message": "Different presentation text"})

    assert warning.identity_key == duplicate.identity_key
    assert sort_findings([warning, error]) == (error, warning)
    assert deduplicate_findings([warning, duplicate, error]) == (error, warning)


def test_summary_calculates_status_and_counts() -> None:
    summary = ValidationSummary.from_findings(
        [finding("INFO", Severity.INFO), finding("WARN", Severity.WARNING)]
    )

    assert summary.status is RunStatus.WARNING
    assert summary.total == 2
    assert summary.counts == {"info": 1, "warning": 1, "error": 0}

    failed = ValidationSummary.from_findings([finding("ERROR", Severity.ERROR)])
    assert failed.status is RunStatus.FAIL


def test_validation_result_normalizes_findings() -> None:
    result = ValidationResult.from_findings(
        project_name="water-demo",
        input_fingerprint="abc123",
        validators=["schema", "mapping"],
        findings=[finding("WARN", Severity.WARNING), finding("WARN", Severity.WARNING)],
    )

    assert result.summary.total == 1
    assert result.validators == ("schema", "mapping")
    assert result.findings[0].code == "WARN"
