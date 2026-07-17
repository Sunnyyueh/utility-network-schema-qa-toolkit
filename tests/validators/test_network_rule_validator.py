from un_schema_qa.models import (
    AssetTypeSpec,
    MappingPair,
    NetworkRuleSpec,
    ProjectData,
    TerminalSpec,
)
from un_schema_qa.validators import NetworkRuleValidator, ValidationContext


def rule(**updates: object) -> NetworkRuleSpec:
    values = {
        "rule_type": "connectivity",
        "from_dataset": "WaterLine",
        "from_asset_group": "Main",
        "from_asset_type": "Distribution Main",
        "to_dataset": "WaterDevice",
        "to_asset_group": "Valve",
        "to_asset_type": "Gate Valve",
        "to_terminal": "Bidirectional",
    }
    values.update(updates)
    return NetworkRuleSpec.model_validate(values)


def project(
    *rules: NetworkRuleSpec,
    include_mapping: bool = False,
) -> ProjectData:
    return ProjectData(
        name="network-rules",
        asset_types=(
            AssetTypeSpec(
                dataset="WaterLine",
                asset_group="Main",
                asset_type="Distribution Main",
            ),
            AssetTypeSpec(
                dataset="WaterDevice",
                asset_group="Valve",
                asset_type="Gate Valve",
                terminals=("Bidirectional",),
            ),
        ),
        terminals=(
            TerminalSpec(
                dataset="WaterDevice",
                asset_group="Valve",
                asset_type="Gate Valve",
                terminal="Bidirectional",
            ),
        ),
        network_rules=rules,
        mappings=(
            (
                MappingPair(
                    mapping_id="mapped-valve",
                    source_dataset="LegacyValve",
                    target_dataset="WaterDevice",
                    asset_group="Valve",
                    asset_type="Gate Valve",
                    rationale="Legacy valve function.",
                )
            ),
        )
        if include_mapping
        else (),
    )


def codes(data: ProjectData) -> set[str]:
    return {item.code for item in NetworkRuleValidator().validate(ValidationContext(project=data))}


def test_network_rule_reports_unknown_assets_and_terminals() -> None:
    invalid = rule(
        from_asset_type="Unknown Main",
        to_terminal="Missing Terminal",
    )

    assert {"NETWORK_RULE_ASSET_UNKNOWN", "NETWORK_RULE_TERMINAL_UNKNOWN"} <= codes(
        project(invalid)
    )


def test_network_rule_reports_invalid_type_and_self_reference() -> None:
    invalid_type = rule(rule_type="teleportation")
    self_reference = rule(
        to_dataset="WaterLine",
        to_asset_group="Main",
        to_asset_type="Distribution Main",
        to_terminal=None,
    )

    assert "NETWORK_RULE_TYPE_UNSUPPORTED" in codes(project(invalid_type))
    assert "NETWORK_RULE_SELF_REFERENCE" in codes(project(self_reference))


def test_network_rule_reports_duplicate_and_reverse_duplicate_rules() -> None:
    forward = rule(to_terminal=None)
    reverse = rule(
        from_dataset="WaterDevice",
        from_asset_group="Valve",
        from_asset_type="Gate Valve",
        to_dataset="WaterLine",
        to_asset_group="Main",
        to_asset_type="Distribution Main",
        to_terminal=None,
    )

    assert "NETWORK_RULE_DUPLICATE" in codes(project(forward, forward.model_copy()))
    assert "NETWORK_RULE_REVERSE_DUPLICATE" in codes(project(forward, reverse))


def test_network_rule_reports_uncovered_mapped_classification() -> None:
    unrelated = rule(
        to_dataset="WaterLine",
        to_asset_group="Main",
        to_asset_type="Distribution Main",
        to_terminal=None,
    )

    assert "NETWORK_RULE_MAPPING_UNCOVERED" in codes(project(unrelated, include_mapping=True))


def test_network_rule_accepts_valid_covered_rule() -> None:
    assert (
        NetworkRuleValidator().validate(
            ValidationContext(project=project(rule(), include_mapping=True))
        )
        == []
    )
