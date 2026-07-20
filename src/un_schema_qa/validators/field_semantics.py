"""Metadata-level semantic checks for source-to-target field mappings."""

from __future__ import annotations

from un_schema_qa.models import FieldMapping, FieldSchema, Finding, MappingPair, Severity
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
                findings.extend(self._field(context, mapping, field_mapping))
        return findings

    def _field(
        self,
        context: ValidationContext,
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
        source_dataset = context.project.source_dataset(mapping.source_dataset)
        target_dataset = context.project.target_dataset(mapping.target_dataset)
        source_field = (
            source_dataset.field(field_mapping.source_field)
            if source_dataset and field_mapping.source_field
            else None
        )
        target_field = target_dataset.field(field_mapping.target_field) if target_dataset else None
        if source_field is None or target_field is None:
            return findings
        if role == "lifecycle_status":
            findings.extend(
                self._lifecycle_status(mapping, field_mapping, source_field, target_field)
            )
        elif role == "owner":
            findings.extend(self._owner(mapping, field_mapping, source_field, target_field))
        return findings

    def _lifecycle_status(
        self,
        mapping: MappingPair,
        field_mapping: FieldMapping,
        source_field: FieldSchema,
        target_field: FieldSchema,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if not source_field.domain:
            findings.append(
                finding(
                    "FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING",
                    Severity.ERROR,
                    self.name,
                    f"Lifecycle source field {source_field.name!r} has no coded-value domain.",
                    "Assign and export the source lifecycle domain, including target_code "
                    "crosswalks where codes differ.",
                    dataset=mapping.source_dataset,
                    field=source_field.name,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={"side": "source"},
                )
            )
        if not target_field.domain:
            findings.append(
                finding(
                    "FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING",
                    Severity.ERROR,
                    self.name,
                    f"Lifecycle target field {target_field.name!r} has no coded-value domain.",
                    "Assign and export the target lifecycle domain so status crosswalks "
                    "can be reviewed.",
                    dataset=mapping.target_dataset,
                    field=target_field.name,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={"side": "target"},
                )
            )
        return findings

    def _owner(
        self,
        mapping: MappingPair,
        field_mapping: FieldMapping,
        source_field: FieldSchema,
        target_field: FieldSchema,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for side, dataset, schema_field in (
            ("source", mapping.source_dataset, source_field),
            ("target", mapping.target_dataset, target_field),
        ):
            if schema_field.data_type.casefold() != "text":
                findings.append(
                    finding(
                        "FIELD_OWNER_TYPE_INVALID",
                        Severity.ERROR,
                        self.name,
                        f"Owner {side} field {schema_field.name!r} uses "
                        f"{schema_field.data_type!r} instead of text.",
                        "Use text fields for owner names or document a separate "
                        "identifier mapping.",
                        dataset=dataset,
                        field=schema_field.name,
                        mapping_id=mapping.mapping_id,
                        location=field_mapping.location,
                        details={
                            "side": side,
                            "data_type": schema_field.data_type,
                        },
                    )
                )
        if (
            source_field.length is not None
            and target_field.length is not None
            and source_field.length > target_field.length
        ):
            findings.append(
                finding(
                    "FIELD_OWNER_LENGTH_RISK",
                    Severity.WARNING,
                    self.name,
                    f"Owner source length {source_field.length} exceeds target length "
                    f"{target_field.length}.",
                    "Increase the target length or document a controlled normalization "
                    "that prevents truncation.",
                    dataset=mapping.target_dataset,
                    field=target_field.name,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={
                        "source_length": source_field.length,
                        "target_length": target_field.length,
                    },
                )
            )
        if bool(source_field.domain) != bool(target_field.domain):
            findings.append(
                finding(
                    "FIELD_OWNER_DOMAIN_ASYMMETRIC",
                    Severity.ERROR,
                    self.name,
                    "Owner mapping declares a coded-value domain on only one side.",
                    "Export and assign owner domains on both sides so the coded-value "
                    "crosswalk can be reviewed, or use text on both sides.",
                    dataset=mapping.target_dataset,
                    field=target_field.name,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                    details={
                        "source_domain": source_field.domain,
                        "target_domain": target_field.domain,
                    },
                )
            )
        return findings
