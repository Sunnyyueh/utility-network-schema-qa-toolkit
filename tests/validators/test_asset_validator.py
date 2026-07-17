from un_schema_qa.models import (
    AssetTypeSpec,
    EngineeringCondition,
    EngineeringContext,
    EngineeringRule,
    MappingPair,
    ProjectData,
)
from un_schema_qa.validators import AssetClassificationValidator, ValidationContext


def rule(rule_id: str, role: str, target: str, priority: int = 100) -> EngineeringRule:
    return EngineeringRule(
        rule_id=rule_id,
        priority=priority,
        conditions=(EngineeringCondition(field="network_role", operator="equals", value=role),),
        target_asset_group="Main",
        target_asset_type=target,
        explanation=f"Network role {role} supports {target}.",
    )


def project(mapping: MappingPair, rules: tuple[EngineeringRule, ...] = ()) -> ProjectData:
    return ProjectData(
        name="assets",
        mappings=(mapping,),
        asset_types=(
            AssetTypeSpec(
                dataset="WaterLine",
                asset_group="Main",
                asset_type="Distribution Main",
            ),
            AssetTypeSpec(
                dataset="WaterLine",
                asset_group="Main",
                asset_type="Transmission Main",
            ),
        ),
        engineering_rules=rules,
    )


def codes(mapping: MappingPair, rules: tuple[EngineeringRule, ...] = ()) -> set[str]:
    return {
        item.code
        for item in AssetClassificationValidator().validate(
            ValidationContext(project=project(mapping, rules))
        )
    }


def mapping(**updates: object) -> MappingPair:
    values = {
        "mapping_id": "water-main",
        "source_dataset": "LegacyLine",
        "target_dataset": "WaterLine",
        "asset_group": "Main",
        "asset_type": "Distribution Main",
        "rationale": "Network role indicates distribution service.",
        "engineering_context": EngineeringContext(network_role="Distribution"),
    }
    values.update(updates)
    return MappingPair.model_validate(values)


def test_asset_validator_reports_incomplete_unknown_and_missing_rationale() -> None:
    incomplete = mapping(asset_type=None)
    unknown = mapping(asset_type="Service Line", rationale=None)

    assert "ASSET_CLASSIFICATION_INCOMPLETE" in codes(incomplete)
    assert {"ASSET_TYPE_UNKNOWN", "ASSET_RATIONALE_MISSING"} <= codes(unknown)


def test_asset_validator_reports_no_rule_match() -> None:
    assert "ASSET_RULE_NO_MATCH" in codes(
        mapping(), (rule("transmission", "Transmission", "Transmission Main"),)
    )


def test_asset_validator_reports_single_explained_match() -> None:
    assert "ASSET_RULE_MATCH" in codes(
        mapping(), (rule("distribution", "Distribution", "Distribution Main"),)
    )


def test_asset_validator_reports_conflicting_rule_targets() -> None:
    rules = (
        rule("distribution", "Distribution", "Distribution Main", 10),
        rule("conflict", "Distribution", "Transmission Main", 20),
    )

    assert "ASSET_RULE_CONFLICT" in codes(mapping(), rules)


def test_asset_validator_reports_mapping_disagreement() -> None:
    rules = (rule("distribution", "Distribution", "Distribution Main"),)

    assert "ASSET_RULE_DISAGREEMENT" in codes(mapping(asset_type="Transmission Main"), rules)


def test_asset_validator_accepts_reviewed_classification_without_rules() -> None:
    assert (
        AssetClassificationValidator().validate(ValidationContext(project=project(mapping()))) == []
    )
