from un_schema_qa.engine import build_default_registry
from un_schema_qa.models import (
    DatasetSchema,
    FieldMapping,
    FieldSchema,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import ValidationContext


def dataset(name: str, *fields: FieldSchema) -> DatasetSchema:
    return DatasetSchema(name=name, geometry_type="polyline", fields=fields)


def semantic_project(*field_mappings: FieldMapping) -> ProjectData:
    return ProjectData(
        name="field-semantics",
        source_datasets=(
            dataset(
                "LegacyLine",
                FieldSchema(name="status", data_type="text"),
                FieldSchema(name="owner", data_type="text", length=100),
                FieldSchema(name="elevation", data_type="double"),
            ),
        ),
        target_datasets=(
            dataset(
                "WaterLine",
                FieldSchema(name="lifecycle_status", data_type="text"),
                FieldSchema(name="owner", data_type="text", length=128),
                FieldSchema(name="elevation", data_type="double"),
            ),
        ),
        mappings=(
            MappingPair(
                mapping_id="semantic-main",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
                field_mappings=field_mappings,
            ),
        ),
    )


def semantic_codes(project: ProjectData) -> set[str]:
    validator = build_default_registry().get("field_semantics")
    assert validator is not None
    return {item.code for item in validator.validate(ValidationContext(project=project))}


def test_default_registry_contains_field_semantics_validator() -> None:
    validator = build_default_registry().get("field_semantics")

    assert validator is not None
    assert validator.required_inputs == (
        "mappings",
        "source_datasets",
        "target_datasets",
    )


def test_field_semantics_reports_unknown_role() -> None:
    project = semantic_project(
        FieldMapping(
            source_field="status",
            target_field="lifecycle_status",
            semantic_role="asset mood",
            field_rationale="Legacy description retained for review.",
        )
    )

    assert "FIELD_SEMANTIC_ROLE_UNKNOWN" in semantic_codes(project)


def test_field_semantics_normalizes_role_and_requires_rationale() -> None:
    project = semantic_project(
        FieldMapping(
            source_field="status",
            target_field="lifecycle_status",
            semantic_role="Lifecycle-Status",
        )
    )

    assert "FIELD_SEMANTIC_RATIONALE_MISSING" in semantic_codes(project)
