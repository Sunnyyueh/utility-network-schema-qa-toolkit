"""Metadata-level semantic checks for source-to-target field mappings."""

from __future__ import annotations

from un_schema_qa.models import FieldMapping, Finding, MappingPair, Severity
from un_schema_qa.normalization import normalize_header

from .base import ValidationContext, finding

_SUPPORTED_ROLES = {"lifecycle_status", "owner", "elevation"}


class FieldSemanticsValidator:
    """Review declared field semantics without evaluating feature records."""

    name: str = "field_semantics"
    required_inputs: tuple[str, ...] = (
        "mappings",
        "source_datasets",
        "target_datasets",
    )

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            for field_mapping in mapping.field_mappings:
                if not field_mapping.semantic_role:
                    continue
                findings.extend(self._field(mapping, field_mapping))
        return findings

    def _field(
        self,
        mapping: MappingPair,
        field_mapping: FieldMapping,
    ) -> list[Finding]:
        role = normalize_header(field_mapping.semantic_role or "")
        if role not in _SUPPORTED_ROLES:
            return [
                finding(
                    "FIELD_SEMANTIC_ROLE_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Field mapping declares unsupported semantic role "
                    f"{field_mapping.semantic_role!r}.",
                    "Use lifecycle_status, owner, or elevation, or leave the role empty.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={"semantic_role": field_mapping.semantic_role},
                )
            ]

        findings: list[Finding] = []
        if not field_mapping.field_rationale:
            findings.append(
                finding(
                    "FIELD_SEMANTIC_RATIONALE_MISSING",
                    Severity.WARNING,
                    self.name,
                    f"{role.replace('_', ' ').title()} mapping has no field rationale.",
                    "Document the intended normalization, crosswalk, conversion, or review.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={"semantic_role": role},
                )
            )
        return findings
