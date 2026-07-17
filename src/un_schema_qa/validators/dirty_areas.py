"""Dirty-area export normalization and remediation grouping."""

from __future__ import annotations

from collections import defaultdict

from un_schema_qa.models import DirtyAreaRecord, Finding, Severity

from .base import ValidationContext, finding


class DirtyAreaValidator:
    name = "dirty_areas"
    required_inputs = ("dirty_areas",)

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        catalog = {
            str(code).casefold(): str(category)
            for code, category in context.options.get("dirty_area_remediation", {}).items()
        }
        grouped: dict[tuple[str, str, str], list[DirtyAreaRecord]] = defaultdict(list)
        for issue in context.project.dirty_areas:
            severity = (issue.severity or "warning").casefold()
            grouped[(issue.dataset.casefold(), issue.error_code.casefold(), severity)].append(issue)
            if not issue.global_id and not issue.object_id:
                findings.append(
                    finding(
                        "DIRTY_AREA_IDENTIFIER_MISSING",
                        Severity.ERROR,
                        self.name,
                        f"Dirty-area issue {issue.error_code!r} has no GlobalID or ObjectID.",
                        "Include at least one feature identifier in the issue export.",
                        dataset=issue.dataset,
                        location=issue.location,
                    )
                )
            if severity not in {item.value for item in Severity}:
                findings.append(
                    finding(
                        "DIRTY_AREA_SEVERITY_INVALID",
                        Severity.WARNING,
                        self.name,
                        f"Dirty-area issue uses unsupported severity {issue.severity!r}.",
                        "Use info, warning, or error.",
                        dataset=issue.dataset,
                        location=issue.location,
                    )
                )
        for issues in grouped.values():
            findings.extend(self._group(issues, catalog))
        return findings

    def _group(self, issues: list[DirtyAreaRecord], catalog: dict[str, str]) -> list[Finding]:
        first = issues[0]
        category = next(
            (issue.remediation_category for issue in issues if issue.remediation_category),
            catalog.get(first.error_code.casefold()),
        )
        findings: list[Finding] = []
        if first.error_code.casefold() not in catalog and not any(
            issue.remediation_category for issue in issues
        ):
            findings.append(
                finding(
                    "DIRTY_AREA_CODE_UNKNOWN",
                    Severity.WARNING,
                    self.name,
                    f"Dirty-area code {first.error_code!r} is not in the remediation catalog.",
                    "Add an explicit project-specific remediation category for the code.",
                    dataset=first.dataset,
                    location=first.location,
                    details={"error_code": first.error_code},
                )
            )
        if category is None:
            findings.append(
                finding(
                    "DIRTY_AREA_REMEDIATION_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"Dirty-area code {first.error_code!r} has no remediation category.",
                    "Assign a reviewed category in the export or project catalog.",
                    dataset=first.dataset,
                    location=first.location,
                    details={"error_code": first.error_code},
                )
            )
        severity_value = (first.severity or "warning").casefold()
        group_severity = (
            Severity(severity_value)
            if severity_value in {item.value for item in Severity}
            else Severity.WARNING
        )
        findings.append(
            finding(
                "DIRTY_AREA_GROUP",
                group_severity,
                self.name,
                f"{len(issues)} dirty-area issue(s) for dataset {first.dataset!r}, "
                f"code {first.error_code!r}.",
                "Review the grouped features and apply the documented remediation.",
                dataset=first.dataset,
                location=first.location,
                details={
                    "error_code": first.error_code,
                    "count": len(issues),
                    "severity": severity_value,
                    "remediation_category": category,
                },
            )
        )
        return findings
