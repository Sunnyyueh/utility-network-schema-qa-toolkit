from un_schema_qa.models import (
    AssetTypeSpec,
    DatasetSchema,
    DomainSpec,
    DomainValue,
    FieldMapping,
    FieldSchema,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import DomainValidator, ValidationContext


def codes(project: ProjectData) -> set[str]:
    return {item.code for item in DomainValidator().validate(ValidationContext(project=project))}


def test_domain_validator_reports_missing_field_domain() -> None:
    project = ProjectData(
        name="missing",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(FieldSchema(name="material", data_type="text", domain="Material"),),
            ),
        ),
    )

    assert "DOMAIN_MISSING" in codes(project)


def test_domain_validator_reports_duplicate_domains_codes_and_descriptions() -> None:
    material = DomainSpec.model_construct(
        name="Material",
        values=(
            DomainValue(code="DI", description="Ductile Iron"),
            DomainValue(code="di", description="Duplicate Code"),
            DomainValue(code="CI", description="Ductile Iron"),
        ),
        field_type="text",
        location=None,
    )
    project = ProjectData.model_construct(
        name="duplicates",
        source_datasets=(),
        target_datasets=(),
        source_domains=(material, material.model_copy()),
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

    assert {
        "DOMAIN_DUPLICATE",
        "DOMAIN_CODE_DUPLICATE",
        "DOMAIN_DESCRIPTION_AMBIGUOUS",
    } <= codes(project)


def test_domain_validator_reports_invalid_coded_default() -> None:
    project = ProjectData(
        name="defaults",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(
                    FieldSchema(
                        name="material",
                        data_type="text",
                        domain="Material",
                        default="UNKNOWN_CODE",
                    ),
                ),
            ),
        ),
        target_domains=(
            DomainSpec(
                name="Material",
                values=(DomainValue(code="DI", description="Ductile Iron"),),
            ),
        ),
    )

    assert "DOMAIN_DEFAULT_INVALID" in codes(project)


def test_domain_validator_reports_unmapped_and_unknown_crosswalk_values() -> None:
    project = ProjectData(
        name="crosswalk",
        source_datasets=(
            DatasetSchema(
                name="LegacyLine",
                fields=(FieldSchema(name="material", data_type="text", domain="LegacyMaterial"),),
            ),
        ),
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(FieldSchema(name="material", data_type="text", domain="TargetMaterial"),),
            ),
        ),
        source_domains=(
            DomainSpec(
                name="LegacyMaterial",
                values=(
                    DomainValue(code="DUCTILE", description="Ductile Iron", target_code="DI"),
                    DomainValue(code="CAST", description="Cast Iron"),
                    DomainValue(code="WOOD", description="Wood Stave", target_code="WOOD"),
                ),
            ),
        ),
        target_domains=(
            DomainSpec(
                name="TargetMaterial",
                values=(DomainValue(code="DI", description="Ductile Iron"),),
            ),
        ),
        mappings=(
            MappingPair(
                mapping_id="material",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
                field_mappings=(FieldMapping(source_field="material", target_field="material"),),
            ),
        ),
    )

    assert {"DOMAIN_VALUE_UNMAPPED", "DOMAIN_TARGET_CODE_UNKNOWN"} <= codes(project)


def test_domain_validator_checks_asset_group_and_type_codes() -> None:
    project = ProjectData(
        name="assets",
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(
                    FieldSchema(name="assetgroup", data_type="integer", domain="AssetGroup"),
                    FieldSchema(name="assettype", data_type="integer", domain="AssetType"),
                ),
                asset_group_field="assetgroup",
                asset_type_field="assettype",
            ),
        ),
        target_domains=(
            DomainSpec(
                name="AssetGroup",
                values=(DomainValue(code="1", description="Main"),),
            ),
            DomainSpec(
                name="AssetType",
                values=(DomainValue(code="2", description="Distribution"),),
            ),
        ),
        asset_types=(
            AssetTypeSpec(
                dataset="WaterLine",
                asset_group="Main",
                asset_type="Transmission",
                asset_group_code="99",
                asset_type_code="98",
            ),
        ),
    )

    assert {"DOMAIN_ASSET_GROUP_CODE_INVALID", "DOMAIN_ASSET_TYPE_CODE_INVALID"} <= codes(project)


def test_domain_validator_accepts_complete_direct_code_coverage() -> None:
    source_domain = DomainSpec(
        name="SourceStatus",
        values=(DomainValue(code="A", description="Active"),),
    )
    target_domain = DomainSpec(
        name="TargetStatus",
        values=(DomainValue(code="A", description="Active"),),
    )
    project = ProjectData(
        name="valid",
        source_datasets=(
            DatasetSchema(
                name="LegacyLine",
                fields=(FieldSchema(name="status", data_type="text", domain="SourceStatus"),),
            ),
        ),
        target_datasets=(
            DatasetSchema(
                name="WaterLine",
                fields=(FieldSchema(name="status", data_type="text", domain="TargetStatus"),),
            ),
        ),
        source_domains=(source_domain,),
        target_domains=(target_domain,),
        mappings=(
            MappingPair(
                mapping_id="status",
                source_dataset="LegacyLine",
                target_dataset="WaterLine",
                field_mappings=(FieldMapping(source_field="status", target_field="status"),),
            ),
        ),
    )

    assert DomainValidator().validate(ValidationContext(project=project)) == []
