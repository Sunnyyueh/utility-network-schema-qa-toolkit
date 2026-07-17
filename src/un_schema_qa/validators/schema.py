"""Source and target schema validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from un_schema_qa.models import DatasetSchema, FieldSchema, Finding, Severity

from .base import ValidationContext, finding

_SUPPORTED_TYPES = {
    "blob",
    "date",
    "datetime",
    "double",
    "float",
    "geometry",
    "globalid",
    "guid",
    "integer",
    "oid",
    "raster",
    "short",
    "text",
}


class SchemaValidator:
    name: str = "schema"
    required_inputs: tuple[str, ...] = ("source_datasets", "target_datasets")

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(self._duplicates(context))
        for scope, datasets in (
            ("source", context.project.source_datasets),
            ("target", context.project.target_datasets),
        ):
            for dataset in datasets:
                findings.extend(self._dataset(dataset, scope))
        findings.extend(self._geometry(context))
        return findings

    def _duplicates(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for scope, datasets in (
            ("source", context.project.source_datasets),
            ("target", context.project.target_datasets),
        ):
            seen: set[str] = set()
            for dataset in datasets:
                key = dataset.name.casefold()
                if key in seen:
                    findings.append(
                        finding(
                            "SCHEMA_DATASET_DUPLICATE",
                            Severity.ERROR,
                            self.name,
                            f"Duplicate {scope} dataset {dataset.name!r}.",
                            "Keep one canonical schema record for each dataset.",
                            dataset=dataset.name,
                            location=dataset.location,
                        )
                    )
                seen.add(key)
        return findings

    def _dataset(self, dataset: DatasetSchema, scope: str) -> list[Finding]:
        findings: list[Finding] = []
        if not dataset.fields:
            findings.append(
                finding(
                    "SCHEMA_FIELDS_MISSING",
                    Severity.ERROR,
                    self.name,
                    f"{scope.title()} dataset {dataset.name!r} has no field inventory.",
                    "Export or provide at least one field definition for the dataset.",
                    dataset=dataset.name,
                    location=dataset.location,
                )
            )
        seen: set[str] = set()
        for schema_field in dataset.fields:
            key = schema_field.name.casefold()
            if key in seen:
                findings.append(
                    finding(
                        "SCHEMA_FIELD_DUPLICATE",
                        Severity.ERROR,
                        self.name,
                        f"Dataset {dataset.name!r} repeats field {schema_field.name!r}.",
                        "Remove or rename the duplicate field definition.",
                        dataset=dataset.name,
                        field=schema_field.name,
                        location=schema_field.location,
                    )
                )
            seen.add(key)
            findings.extend(self._field(dataset, schema_field))
        findings.extend(self._field_references(dataset))
        return findings

    def _field(self, dataset: DatasetSchema, schema_field: FieldSchema) -> list[Finding]:
        findings: list[Finding] = []
        if schema_field.data_type.casefold() not in _SUPPORTED_TYPES:
            findings.append(
                finding(
                    "SCHEMA_TYPE_UNSUPPORTED",
                    Severity.ERROR,
                    self.name,
                    f"Field {schema_field.name!r} uses unsupported type "
                    f"{schema_field.data_type!r}.",
                    "Use a documented normalized field type or add an explicit conversion.",
                    dataset=dataset.name,
                    field=schema_field.name,
                    location=schema_field.location,
                )
            )
        if schema_field.required and schema_field.nullable:
            findings.append(
                finding(
                    "SCHEMA_REQUIRED_NULLABLE",
                    Severity.WARNING,
                    self.name,
                    f"Required field {schema_field.name!r} is also marked nullable.",
                    "Confirm the target requirement and align required/nullability metadata.",
                    dataset=dataset.name,
                    field=schema_field.name,
                    location=schema_field.location,
                )
            )
        if schema_field.default is not None and not _valid_default(schema_field):
            findings.append(
                finding(
                    "SCHEMA_DEFAULT_INVALID",
                    Severity.ERROR,
                    self.name,
                    f"Default for field {schema_field.name!r} is incompatible with "
                    f"{schema_field.data_type!r}.",
                    "Use a default value compatible with the declared field type.",
                    dataset=dataset.name,
                    field=schema_field.name,
                    location=schema_field.location,
                )
            )
        return findings

    def _field_references(self, dataset: DatasetSchema) -> list[Finding]:
        findings: list[Finding] = []
        references = (
            (
                "subtype_field",
                dataset.subtype_field,
                "SCHEMA_SUBTYPE_FIELD_UNKNOWN",
            ),
            (
                "asset_group_field",
                dataset.asset_group_field,
                "SCHEMA_ASSET_GROUP_FIELD_UNKNOWN",
            ),
            (
                "asset_type_field",
                dataset.asset_type_field,
                "SCHEMA_ASSET_TYPE_FIELD_UNKNOWN",
            ),
        )
        for label, field_name, code in references:
            if field_name and dataset.field(field_name) is None:
                findings.append(
                    finding(
                        code,
                        Severity.ERROR,
                        self.name,
                        f"Dataset {dataset.name!r} references unknown {label} {field_name!r}.",
                        "Add the referenced field or correct the schema metadata.",
                        dataset=dataset.name,
                        field=field_name,
                        location=dataset.location,
                    )
                )
        return findings

    def _geometry(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            source = context.project.source_dataset(mapping.source_dataset)
            target = context.project.target_dataset(mapping.target_dataset)
            if (
                source
                and target
                and source.geometry_type
                and target.geometry_type
                and source.geometry_type.casefold() != target.geometry_type.casefold()
            ):
                findings.append(
                    finding(
                        "SCHEMA_GEOMETRY_MISMATCH",
                        Severity.ERROR,
                        self.name,
                        f"Mapping {mapping.mapping_id!r} routes {source.geometry_type} "
                        f"geometry to {target.geometry_type} geometry.",
                        "Select a geometry-compatible target or document a supported conversion.",
                        dataset=target.name,
                        mapping_id=mapping.mapping_id,
                        location=mapping.location,
                    )
                )
        return findings


def _valid_default(schema_field: FieldSchema) -> bool:
    value: Any = schema_field.default
    data_type = schema_field.data_type.casefold()
    if data_type in {"short", "integer", "oid"}:
        if isinstance(value, bool):
            return False
        try:
            int(str(value))
        except ValueError:
            return False
        return True
    if data_type in {"float", "double"}:
        if isinstance(value, bool):
            return False
        try:
            float(value)
        except (TypeError, ValueError):
            return False
        return True
    if data_type in {"date", "datetime"}:
        if isinstance(value, (date, datetime)):
            return True
        try:
            datetime.fromisoformat(str(value))
        except ValueError:
            return False
        return True
    if data_type in {"text", "guid", "globalid"}:
        return isinstance(value, str)
    return True
