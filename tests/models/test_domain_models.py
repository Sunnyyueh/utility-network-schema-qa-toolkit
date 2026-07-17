import pytest
from pydantic import ValidationError

from un_schema_qa.models import (
    AssetTypeSpec,
    DatasetSchema,
    DomainSpec,
    DomainValue,
    EngineeringContext,
    FieldMapping,
    FieldSchema,
    MappingPair,
    ProjectData,
)


def field(name: str, data_type: str = "text") -> FieldSchema:
    return FieldSchema(name=name, data_type=data_type)


def dataset(name: str, *fields: FieldSchema) -> DatasetSchema:
    return DatasetSchema(name=name, geometry_type="polyline", fields=fields)


def test_dataset_and_project_lookups_are_case_insensitive() -> None:
    source = dataset("LegacyWaterLine", field("Material"), field("Diameter", "double"))
    target = dataset("WaterLine", field("material"), field("diameter", "double"))
    domain = DomainSpec(
        name="MaterialDomain",
        values=(DomainValue(code="DI", description="Ductile Iron"),),
    )
    asset = AssetTypeSpec(
        dataset="WaterLine",
        asset_group="Main",
        asset_type="Transmission",
        asset_group_code="1",
        asset_type_code="2",
    )
    project = ProjectData(
        name="water",
        source_datasets=(source,),
        target_datasets=(target,),
        target_domains=(domain,),
        asset_types=(asset,),
    )

    assert source.field("material").name == "Material"
    assert project.source_dataset("legacywaterline") is source
    assert project.target_domain("materialdomain") is domain
    assert project.asset_type("waterline", "main", "transmission") is asset
    assert project.target_dataset("missing") is None


def test_mapping_and_engineering_context_preserve_review_data() -> None:
    context = EngineeringContext(
        network_role="Transmission",
        nominal_diameter=24.0,
        extra={"pressure_zone": "North"},
    )
    mapping = MappingPair(
        mapping_id="water-main",
        source_dataset="LegacyWaterLine",
        target_dataset="WaterLine",
        definition_query="network_role = 'Transmission'",
        purpose="Select transmission mains",
        expected_count=12,
        field_mappings=(FieldMapping(source_field="Material", target_field="material"),),
        asset_group="Main",
        asset_type="Transmission",
        rationale="Network role and operating pressure identify the class.",
        engineering_context=context,
    )

    assert mapping.engineering_context is not None
    assert mapping.engineering_context.value("NETWORK_ROLE") == "Transmission"
    assert mapping.engineering_context.value("pressure_zone") == "North"


def test_duplicate_names_are_rejected() -> None:
    duplicate = dataset("WaterLine", field("material"))

    with pytest.raises(ValidationError, match="duplicate target dataset"):
        ProjectData(name="water", target_datasets=(duplicate, duplicate))


def test_optional_inventories_default_to_empty_tuples() -> None:
    project = ProjectData(name="minimal")

    assert project.mappings == ()
    assert project.dirty_areas == ()
    assert project.engineering_rules == ()
