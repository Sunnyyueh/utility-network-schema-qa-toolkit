from un_schema_qa.models import DatasetSchema, FieldSchema, MappingPair, ProjectData
from un_schema_qa.validators import SchemaValidator, ValidationContext


def field(
    name: str,
    data_type: str = "text",
    *,
    required: bool = False,
    nullable: bool = True,
    default: object = None,
) -> FieldSchema:
    return FieldSchema(
        name=name,
        data_type=data_type,
        required=required,
        nullable=nullable,
        default=default,
    )


def codes(project: ProjectData) -> set[str]:
    return {
        finding.code for finding in SchemaValidator().validate(ValidationContext(project=project))
    }


def test_schema_validator_reports_duplicate_datasets_and_fields() -> None:
    duplicate_fields = DatasetSchema.model_construct(
        name="Line",
        geometry_type="polyline",
        fields=(field("Material"), field("material")),
    )
    duplicate_datasets = ProjectData.model_construct(
        name="duplicate",
        source_datasets=(duplicate_fields,),
        target_datasets=(
            DatasetSchema(name="WaterLine", fields=(field("id"),)),
            DatasetSchema(name="waterline", fields=(field("id"),)),
        ),
        source_domains=(),
        target_domains=(),
        mappings=(),
        asset_types=(),
        data_reference=(),
        attribute_rules=(),
        network_rules=(),
        terminals=(),
        dirty_areas=(),
        engineering_rules=(),
        profile=None,
    )

    assert {"SCHEMA_DATASET_DUPLICATE", "SCHEMA_FIELD_DUPLICATE"} <= codes(duplicate_datasets)


def test_schema_validator_reports_unsupported_types_and_empty_datasets() -> None:
    project = ProjectData(
        name="invalid-types",
        source_datasets=(DatasetSchema(name="Legacy", fields=(field("shape", "hypervector"),)),),
        target_datasets=(DatasetSchema(name="Empty"),),
    )

    assert {"SCHEMA_TYPE_UNSUPPORTED", "SCHEMA_FIELDS_MISSING"} <= codes(project)


def test_schema_validator_reports_required_nullable_and_invalid_default() -> None:
    project = ProjectData(
        name="invalid-fields",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(
                    field("material", required=True, nullable=True),
                    field("diameter", "double", default="not-a-number"),
                ),
            ),
        ),
    )

    assert {"SCHEMA_REQUIRED_NULLABLE", "SCHEMA_DEFAULT_INVALID"} <= codes(project)


def test_schema_validator_reports_geometry_mismatch_for_mapped_datasets() -> None:
    project = ProjectData(
        name="geometry",
        source_datasets=(
            DatasetSchema(
                name="LegacyLine",
                geometry_type="polyline",
                fields=(field("id", "integer"),),
            ),
        ),
        target_datasets=(
            DatasetSchema(
                name="WaterDevice",
                geometry_type="point",
                fields=(field("id", "integer"),),
            ),
        ),
        mappings=(
            MappingPair(
                mapping_id="line-device",
                source_dataset="LegacyLine",
                target_dataset="WaterDevice",
            ),
        ),
    )

    assert "SCHEMA_GEOMETRY_MISMATCH" in codes(project)


def test_schema_validator_reports_unknown_subtype_and_asset_fields() -> None:
    project = ProjectData(
        name="references",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(field("material"),),
                subtype_field="subtype_code",
                asset_group_field="assetgroup",
                asset_type_field="assettype",
            ),
        ),
    )

    assert {
        "SCHEMA_SUBTYPE_FIELD_UNKNOWN",
        "SCHEMA_ASSET_GROUP_FIELD_UNKNOWN",
        "SCHEMA_ASSET_TYPE_FIELD_UNKNOWN",
    } <= codes(project)


def test_schema_validator_accepts_compatible_schema() -> None:
    project = ProjectData(
        name="valid",
        source_datasets=(
            DatasetSchema(
                name="LegacyLine",
                geometry_type="polyline",
                fields=(field("material"), field("diameter", "double")),
            ),
        ),
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                geometry_type="polyline",
                fields=(
                    field("material", required=True, nullable=False, default="Unknown"),
                    field("diameter", "double"),
                    field("assetgroup", "integer"),
                    field("assettype", "integer"),
                ),
                asset_group_field="assetgroup",
                asset_type_field="assettype",
            ),
        ),
        mappings=(
            MappingPair(
                mapping_id="line",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
            ),
        ),
    )

    assert SchemaValidator().validate(ValidationContext(project=project)) == []
