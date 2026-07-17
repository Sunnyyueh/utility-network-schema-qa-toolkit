"""Data Reference inventory validation."""

from __future__ import annotations

from pathlib import Path

from un_schema_qa.models import DataReferenceEntry, Finding, Severity

from .base import ValidationContext, finding


class DataReferenceValidator:
    name: str = "data_reference"
    required_inputs: tuple[str, ...] = ("data_reference",)

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[tuple[str, ...]] = set()
        for entry in context.project.data_reference:
            findings.extend(self._entry(context, entry))
            if entry.enabled:
                key = (
                    entry.source.casefold(),
                    entry.target.casefold(),
                    entry.mapping_workbook.casefold(),
                    (entry.mapping_id or "").casefold(),
                    _normalized_query(entry.definition_query),
                )
                if key in seen:
                    findings.append(
                        finding(
                            "DATAREF_DUPLICATE",
                            Severity.ERROR,
                            self.name,
                            f"Duplicate enabled Data Reference row for {entry.source!r} "
                            f"to {entry.target!r}.",
                            "Keep one enabled row for each source, target, and workbook.",
                            dataset=entry.target or None,
                            mapping_id=entry.mapping_id,
                            location=entry.location,
                        )
                    )
                seen.add(key)
        return findings

    def _entry(self, context: ValidationContext, entry: DataReferenceEntry) -> list[Finding]:
        findings: list[Finding] = []
        if not entry.enabled:
            findings.append(
                finding(
                    "DATAREF_DISABLED",
                    Severity.INFO,
                    self.name,
                    f"Data Reference row for {entry.source!r} to {entry.target!r} is disabled.",
                    "Confirm the row is intentionally excluded from the load configuration.",
                    dataset=entry.target or None,
                    mapping_id=entry.mapping_id,
                    location=entry.location,
                )
            )
        missing = [
            label
            for label, value in (
                ("source", entry.source),
                ("target", entry.target),
                ("mapping_workbook", entry.mapping_workbook),
            )
            if not value.strip()
        ]
        if missing:
            findings.append(
                finding(
                    "DATAREF_REQUIRED_VALUE_MISSING",
                    Severity.ERROR,
                    self.name,
                    f"Data Reference row is missing: {', '.join(missing)}.",
                    "Provide source, target, and mapping workbook values.",
                    dataset=entry.target or None,
                    mapping_id=entry.mapping_id,
                    location=entry.location,
                    details={"missing": missing},
                )
            )
        if entry.mapping_workbook.strip() and context.config:
            workbook = Path(entry.mapping_workbook).expanduser()
            if not workbook.is_absolute():
                workbook = context.config.manifest_path.parent / workbook
            if not workbook.is_file():
                findings.append(
                    finding(
                        "DATAREF_WORKBOOK_MISSING",
                        Severity.ERROR,
                        self.name,
                        f"Mapping workbook does not exist: {workbook.resolve()}.",
                        "Correct the path or add the mapping workbook beside the manifest.",
                        dataset=entry.target or None,
                        mapping_id=entry.mapping_id,
                        location=entry.location,
                        details={"path": str(workbook.resolve())},
                    )
                )
        if entry.mapping_id:
            mapping = next(
                (
                    candidate
                    for candidate in context.project.mappings
                    if candidate.mapping_id.casefold() == entry.mapping_id.casefold()
                ),
                None,
            )
            if mapping is None:
                findings.append(
                    finding(
                        "DATAREF_MAPPING_UNKNOWN",
                        Severity.ERROR,
                        self.name,
                        f"Data Reference row uses unknown mapping ID {entry.mapping_id!r}.",
                        "Use a mapping ID from the source-to-target mapping inventory.",
                        dataset=entry.target or None,
                        mapping_id=entry.mapping_id,
                        location=entry.location,
                    )
                )
            else:
                if (
                    mapping.source_dataset.casefold() != entry.source.casefold()
                    or mapping.target_dataset.casefold() != entry.target.casefold()
                ):
                    findings.append(
                        finding(
                            "DATAREF_MAPPING_DATASET_MISMATCH",
                            Severity.ERROR,
                            self.name,
                            f"Data Reference datasets do not match mapping {mapping.mapping_id!r}.",
                            "Align the source/target names with the referenced mapping.",
                            dataset=entry.target or None,
                            mapping_id=entry.mapping_id,
                            location=entry.location,
                        )
                    )
                if _normalized_query(mapping.definition_query) != _normalized_query(
                    entry.definition_query
                ):
                    findings.append(
                        finding(
                            "DATAREF_FILTER_MISMATCH",
                            Severity.ERROR,
                            self.name,
                            f"Data Reference filter differs from mapping {mapping.mapping_id!r}.",
                            "Use the same source-side filter in both reviewed artifacts.",
                            dataset=entry.target or None,
                            mapping_id=entry.mapping_id,
                            location=entry.location,
                        )
                    )
        return findings


def _normalized_query(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()
