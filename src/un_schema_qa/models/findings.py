"""Validation findings and run summaries."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from pydantic import Field, field_validator

from un_schema_qa.version import __version__

from .common import RunStatus, Severity, SourceLocation, StrictModel


class Finding(StrictModel):
    """One actionable validation observation."""

    code: str
    severity: Severity
    validator: str
    message: str
    recommendation: str
    dataset: str | None = None
    field: str | None = None
    mapping_id: str | None = None
    location: SourceLocation | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("finding code cannot be empty")
        return normalized

    @property
    def identity_key(self) -> tuple[object, ...]:
        location = self.location
        return (
            self.code,
            self.validator.casefold(),
            (self.dataset or "").casefold(),
            (self.field or "").casefold(),
            (self.mapping_id or "").casefold(),
            location.path if location else "",
            location.sheet or "" if location else "",
            location.row or 0 if location else 0,
            location.column or "" if location else "",
        )

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (
            -self.severity.rank,
            self.validator.casefold(),
            (self.dataset or "").casefold(),
            (self.field or "").casefold(),
            (self.mapping_id or "").casefold(),
            self.location.path if self.location else "",
            self.location.row or 0 if self.location else 0,
            self.code,
        )


def sort_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Return findings in deterministic report order."""

    return tuple(sorted(findings, key=lambda finding: finding.sort_key))


def deduplicate_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Remove duplicate findings while retaining the first observation."""

    unique: dict[tuple[object, ...], Finding] = {}
    for finding in findings:
        unique.setdefault(finding.identity_key, finding)
    return sort_findings(unique.values())


class ValidationSummary(StrictModel):
    """Aggregate finding counts and run status."""

    status: RunStatus
    total: int = Field(ge=0)
    counts: dict[str, int]

    @classmethod
    def from_findings(cls, findings: Iterable[Finding]) -> ValidationSummary:
        materialized = tuple(findings)
        counts = {severity.value: 0 for severity in Severity}
        for finding in materialized:
            counts[finding.severity.value] += 1
        if counts[Severity.ERROR.value]:
            status = RunStatus.FAIL
        elif counts[Severity.WARNING.value]:
            status = RunStatus.WARNING
        else:
            status = RunStatus.PASS
        return cls(status=status, total=len(materialized), counts=counts)


class ValidationResult(StrictModel):
    """Complete deterministic result returned by the public API."""

    schema_version: str = "1.0"
    toolkit_version: str = __version__
    project_name: str
    input_fingerprint: str
    validators: tuple[str, ...]
    findings: tuple[Finding, ...]
    summary: ValidationSummary

    @classmethod
    def from_findings(
        cls,
        *,
        project_name: str,
        input_fingerprint: str,
        validators: Sequence[str],
        findings: Iterable[Finding],
    ) -> ValidationResult:
        normalized = deduplicate_findings(findings)
        return cls(
            project_name=project_name,
            input_fingerprint=input_fingerprint,
            validators=tuple(validators),
            findings=normalized,
            summary=ValidationSummary.from_findings(normalized),
        )
