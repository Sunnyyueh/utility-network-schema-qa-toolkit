"""Source-to-target field mapping validation."""

from __future__ import annotations

from un_schema_qa.models import FieldMapping, Finding, MappingPair, Severity

from .base import ValidationContext, finding, types_compatible


class MappingValidator:
    name: str = "mapping"
    required_inputs: tuple[str, ...] = (
        "mappings",
        "source_datasets",
        "target_datasets",
    )

    def validate(self, context: ValidationContext) -> list[Finding]:
        findings: list[Finding] = []
        for mapping in context.project.mappings:
            findings.extend(self._mapping(context, mapping))
        return findings

    def _mapping(self, context: ValidationContext, mapping: MappingPair) -> list[Finding]:
        findings: list[Finding] = []
        project = context.project
        source = project.source_dataset(mapping.source_dataset)
        target = project.target_dataset(mapping.target_dataset)
        if not mapping.enabled:
            findings.append(
                finding(
                    "MAP_DISABLED",
                    Severity.INFO,
                    self.name,
                    f"Mapping {mapping.mapping_id!r} is disabled.",
                    "Confirm the row is intentionally excluded from loading.",
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if source is None:
            findings.append(
                finding(
                    "MAP_SOURCE_DATASET_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Mapping {mapping.mapping_id!r} references unknown source dataset "
                    f"{mapping.source_dataset!r}.",
                    "Correct the source dataset name or add its schema inventory.",
                    dataset=mapping.source_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )
        if target is None:
            findings.append(
                finding(
                    "MAP_TARGET_DATASET_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Mapping {mapping.mapping_id!r} references unknown target dataset "
                    f"{mapping.target_dataset!r}.",
                    "Correct the target dataset name or add its schema inventory.",
                    dataset=mapping.target_dataset,
                    mapping_id=mapping.mapping_id,
                    location=mapping.location,
                )
            )

        mapped_targets: set[str] = set()
        for field_mapping in mapping.field_mappings:
            target_key = field_mapping.target_field.casefold()
            if target_key in mapped_targets:
                findings.append(
                    finding(
                        "MAP_TARGET_FIELD_DUPLICATE",
                        Severity.ERROR,
                        self.name,
                        f"Mapping {mapping.mapping_id!r} assigns target field "
                        f"{field_mapping.target_field!r} more than once.",
                        "Keep one unambiguous mapping for each target field.",
                        dataset=mapping.target_dataset,
                        field=field_mapping.target_field,
                        mapping_id=mapping.mapping_id,
                        location=field_mapping.location,
                    )
                )
            mapped_targets.add(target_key)
            findings.extend(self._field(context, mapping, field_mapping))

        if target:
            for target_field in target.fields:
                if (
                    target_field.required
                    and target_field.default is None
                    and target_field.name.casefold() not in mapped_targets
                ):
                    findings.append(
                        finding(
                            "MAP_REQUIRED_TARGET_UNMAPPED",
                            Severity.ERROR,
                            self.name,
                            f"Required target field {target_field.name!r} is not mapped.",
                            "Map the field or define a valid target default.",
                            dataset=target.name,
                            field=target_field.name,
                            mapping_id=mapping.mapping_id,
                            location=mapping.location,
                        )
                    )
        return findings

    def _field(
        self,
        context: ValidationContext,
        mapping: MappingPair,
        field_mapping: FieldMapping,
    ) -> list[Finding]:
        findings: list[Finding] = []
        source = context.project.source_dataset(mapping.source_dataset)
        target = context.project.target_dataset(mapping.target_dataset)
        source_field = (
            source.field(field_mapping.source_field)
            if source and field_mapping.source_field
            else None
        )
        target_field = target.field(field_mapping.target_field) if target else None

        if field_mapping.source_field and source and source_field is None:
            findings.append(
                finding(
                    "MAP_SOURCE_FIELD_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Source field {field_mapping.source_field!r} does not exist in "
                    f"{source.name!r}.",
                    "Correct the source field name or update the schema inventory.",
                    dataset=source.name,
                    field=field_mapping.source_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        if target and target_field is None:
            findings.append(
                finding(
                    "MAP_TARGET_FIELD_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Target field {field_mapping.target_field!r} does not exist in "
                    f"{target.name!r}.",
                    "Correct the target field name or update the schema inventory.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        if (
            source_field
            and target_field
            and not field_mapping.expression
            and not field_mapping.lookup
            and not types_compatible(source_field.data_type, target_field.data_type)
        ):
            findings.append(
                finding(
                    "MAP_TYPE_INCOMPATIBLE",
                    Severity.ERROR,
                    self.name,
                    f"Field {source_field.name!r} ({source_field.data_type}) is not "
                    f"directly compatible with {target_field.name!r} "
                    f"({target_field.data_type}).",
                    "Add a documented conversion or select a compatible target field.",
                    dataset=mapping.target_dataset,
                    field=target_field.name,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        if (
            not field_mapping.source_field
            and not field_mapping.expression
            and field_mapping.default is None
        ):
            findings.append(
                finding(
                    "MAP_INPUT_MISSING",
                    Severity.ERROR,
                    self.name,
                    f"Target field {field_mapping.target_field!r} has no source, "
                    "expression, or default.",
                    "Provide a source field, documented expression, or explicit default.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        if field_mapping.expression and field_mapping.lookup:
            findings.append(
                finding(
                    "MAP_TRANSFORM_CONFLICT",
                    Severity.ERROR,
                    self.name,
                    f"Target field {field_mapping.target_field!r} declares both an "
                    "expression and lookup.",
                    "Choose one transformation path or split it into documented stages.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        if field_mapping.lookup and not (
            context.project.source_domain(field_mapping.lookup)
            or context.project.target_domain(field_mapping.lookup)
        ):
            findings.append(
                finding(
                    "MAP_LOOKUP_UNKNOWN",
                    Severity.ERROR,
                    self.name,
                    f"Lookup {field_mapping.lookup!r} is not present in the domain inventory.",
                    "Add the lookup/domain definition or correct its name.",
                    dataset=mapping.target_dataset,
                    field=field_mapping.target_field,
                    mapping_id=mapping.mapping_id,
                    location=field_mapping.location,
                )
            )
        return findings
