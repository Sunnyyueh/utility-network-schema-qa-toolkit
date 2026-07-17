from un_schema_qa.models import (
    DatasetSchema,
    DomainSpec,
    FieldMapping,
    FieldSchema,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import MappingValidator, ValidationContext


def dataset(name: str, *fields: FieldSchema) -> DatasetSchema:
    return DatasetSchema(name=name, geometry_type="polyline", fields=fields)


def project_with(mapping: MappingPair) -> ProjectData:
    return ProjectData(
        name="mapping",
        source_datasets=(
            dataset(
                "LegacyLine",
                FieldSchema(name="material", data_type="text"),
                FieldSchema(name="diameter", data_type="double"),
            ),
        ),
        target_datasets=(
            dataset(
                "WaterLine",
                FieldSchema(name="material", data_type="text", required=True, nullable=False),
                FieldSchema(name="diameter", data_type="double"),
            ),
        ),
        target_domains=(DomainSpec(name="MaterialCrosswalk"),),
        mappings=(mapping,),
    )


def codes(project: ProjectData) -> set[str]:
    return {item.code for item in MappingValidator().validate(ValidationContext(project=project))}


def test_mapping_validator_reports_unknown_datasets() -> None:
    mapping = MappingPair(
        mapping_id="unknown",
        source_dataset="MissingSource",
        target_dataset="MissingTarget",
    )

    assert {
        "MAP_SOURCE_DATASET_UNKNOWN",
        "MAP_TARGET_DATASET_UNKNOWN",
    } <= codes(project_with(mapping))


def test_mapping_validator_reports_unknown_fields_and_unmapped_required_target() -> None:
    mapping = MappingPair(
        mapping_id="fields",
        source_dataset="LegacyLine",
        target_dataset="WaterLine",
        field_mappings=(FieldMapping(source_field="missing", target_field="unknown_target"),),
    )

    assert {
        "MAP_SOURCE_FIELD_UNKNOWN",
        "MAP_TARGET_FIELD_UNKNOWN",
        "MAP_REQUIRED_TARGET_UNMAPPED",
    } <= codes(project_with(mapping))


def test_mapping_validator_reports_type_and_duplicate_target_conflicts() -> None:
    mapping = MappingPair(
        mapping_id="types",
        source_dataset="LegacyLine",
        target_dataset="WaterLine",
        field_mappings=(
            FieldMapping(source_field="diameter", target_field="material"),
            FieldMapping(source_field="material", target_field="material"),
        ),
    )

    assert {"MAP_TYPE_INCOMPATIBLE", "MAP_TARGET_FIELD_DUPLICATE"} <= codes(project_with(mapping))


def test_mapping_validator_reports_incomplete_and_conflicting_transformations() -> None:
    mapping = MappingPair(
        mapping_id="expressions",
        source_dataset="LegacyLine",
        target_dataset="WaterLine",
        field_mappings=(
            FieldMapping(target_field="material"),
            FieldMapping(
                source_field="diameter",
                target_field="diameter",
                expression="diameter * 0.001",
                lookup="MaterialCrosswalk",
            ),
        ),
    )

    assert {"MAP_INPUT_MISSING", "MAP_TRANSFORM_CONFLICT"} <= codes(project_with(mapping))


def test_mapping_validator_reports_unknown_lookup_and_disabled_mapping() -> None:
    mapping = MappingPair(
        mapping_id="disabled",
        source_dataset="LegacyLine",
        target_dataset="WaterLine",
        enabled=False,
        field_mappings=(
            FieldMapping(
                source_field="material",
                target_field="material",
                lookup="MissingCrosswalk",
            ),
        ),
    )

    assert {"MAP_LOOKUP_UNKNOWN", "MAP_DISABLED"} <= codes(project_with(mapping))


def test_mapping_validator_accepts_complete_mapping() -> None:
    mapping = MappingPair(
        mapping_id="complete",
        source_dataset="LegacyLine",
        target_dataset="WaterLine",
        field_mappings=(
            FieldMapping(source_field="material", target_field="material"),
            FieldMapping(source_field="diameter", target_field="diameter"),
        ),
    )

    assert MappingValidator().validate(ValidationContext(project=project_with(mapping))) == []
