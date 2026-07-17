from pathlib import Path

import pytest

from un_schema_qa.exceptions import InputFormatError
from un_schema_qa.models import EngineeringCondition, EngineeringContext, EngineeringRule
from un_schema_qa.rules import evaluate_engineering_rules, load_engineering_rules

FIXTURES = Path(__file__).parent / "fixtures" / "rules"


def make_rule(
    operator: str,
    expected: object,
    *,
    field: str = "network_role",
    rule_id: str = "candidate",
    target: str = "Distribution Main",
    priority: int = 100,
) -> EngineeringRule:
    return EngineeringRule(
        rule_id=rule_id,
        priority=priority,
        conditions=(EngineeringCondition(field=field, operator=operator, value=expected),),
        target_asset_group="Main",
        target_asset_type=target,
        explanation=f"{field} {operator} {expected}",
    )


def test_load_engineering_rules_with_locations_and_priority_order() -> None:
    rules = load_engineering_rules(FIXTURES / "engineering.yml")

    assert [rule.rule_id for rule in rules] == [
        "wastewater-gravity-main",
        "wastewater-force-main",
    ]
    assert rules[0].location is not None
    assert rules[0].location.path.endswith("engineering.yml")


@pytest.mark.parametrize(
    ("operator", "actual", "expected"),
    [
        ("equals", "Distribution", "distribution"),
        ("not_equals", "Transmission", "distribution"),
        ("in", "DI", ["PVC", "DI"]),
        ("not_in", "Copper", ["PVC", "DI"]),
        ("greater_than", 30.0, 20),
        ("greater_or_equal", 20.0, 20),
        ("less_than", 10.0, 20),
        ("less_or_equal", 20.0, 20),
        ("exists", "Active", True),
        ("contains", "Pump Discharge Main", "discharge"),
    ],
)
def test_every_allowed_operator_matches(operator: str, actual: object, expected: object) -> None:
    context = EngineeringContext(extra={"candidate_value": actual})
    rule = make_rule(operator, expected, field="candidate_value")

    evaluation = evaluate_engineering_rules(context, (rule,))

    assert [match.rule_id for match in evaluation.matches] == ["candidate"]
    assert evaluation.missing_attributes == ()


def test_exists_false_can_match_missing_attribute_but_missing_is_disclosed() -> None:
    rule = make_rule("exists", False, field="unknown_attribute")

    evaluation = evaluate_engineering_rules(EngineeringContext(), (rule,))

    assert [match.rule_id for match in evaluation.matches] == ["candidate"]
    assert evaluation.missing_attributes == ("unknown_attribute",)


def test_all_and_any_condition_modes_are_deterministic() -> None:
    conditions = (
        EngineeringCondition(field="flow_regime", operator="equals", value="gravity"),
        EngineeringCondition(field="slope", operator="greater_than", value=0),
    )
    all_rule = EngineeringRule(
        rule_id="all",
        match="all",
        conditions=conditions,
        target_asset_group="Main",
        target_asset_type="Gravity Main",
        explanation="Both conditions are required.",
    )
    any_rule = all_rule.model_copy(update={"rule_id": "any", "match": "any", "priority": 10})
    context = EngineeringContext(flow_regime="gravity", slope=-0.01)

    evaluation = evaluate_engineering_rules(context, (all_rule, any_rule))

    assert [match.rule_id for match in evaluation.matches] == ["any"]


def test_no_match_single_match_and_conflicting_match_states() -> None:
    context = EngineeringContext(network_role="Distribution")
    distribution = make_rule("equals", "Distribution", priority=20)
    duplicate_target = make_rule(
        "in",
        ["Distribution", "Transmission"],
        rule_id="broad",
        priority=10,
    )
    conflicting = make_rule(
        "equals",
        "Distribution",
        rule_id="conflict",
        target="Transmission Main",
        priority=30,
    )

    no_match = evaluate_engineering_rules(
        context, (make_rule("equals", "Service", rule_id="service"),)
    )
    single = evaluate_engineering_rules(context, (distribution,))
    conflict = evaluate_engineering_rules(context, (distribution, conflicting, duplicate_target))

    assert no_match.status == "no_match"
    assert single.status == "single_match"
    assert conflict.status == "conflicting_matches"
    assert [match.rule_id for match in conflict.matches] == [
        "broad",
        "candidate",
        "conflict",
    ]
    assert conflict.explanations[0].startswith("broad:")


def test_multiple_rules_for_same_target_are_not_a_conflict() -> None:
    context = EngineeringContext(network_role="Distribution")
    rules = (
        make_rule("equals", "Distribution", rule_id="exact"),
        make_rule("in", ["Distribution"], rule_id="set"),
    )

    evaluation = evaluate_engineering_rules(context, rules)

    assert evaluation.status == "multiple_matches"
    assert evaluation.conflicting_targets == ()


def test_invalid_operator_is_rejected_when_rules_are_loaded(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(
        """
rules:
  - rule_id: invalid
    conditions:
      - field: slope
        operator: approximately
        value: 0.01
    target_asset_group: Main
    target_asset_type: Gravity Main
    explanation: Invalid test rule.
""",
        encoding="utf-8",
    )

    with pytest.raises(InputFormatError, match="approximately"):
        load_engineering_rules(path)
