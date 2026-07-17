import pytest

from un_schema_qa.filters import analyze_filter, possible_overlap


@pytest.mark.parametrize(
    ("expression", "identifiers", "operator", "values"),
    [
        ("network_role = 'Transmission'", ("network_role",), "=", ("Transmission",)),
        ("diameter_mm >= 600", ("diameter_mm",), ">=", ("600",)),
        ("material IN ('DI', 'PVC')", ("material",), "IN", ("DI", "PVC")),
        ("asset_name LIKE 'FM-%'", ("asset_name",), "LIKE", ("FM-%",)),
        ("retired_on IS NULL", ("retired_on",), "IS NULL", ()),
        ("status IS NOT NULL", ("status",), "IS NOT NULL", ()),
        (
            "installed_on >= DATE '2020-01-01'",
            ("installed_on",),
            ">=",
            ("DATE 2020-01-01",),
        ),
    ],
)
def test_analyze_supported_predicates(
    expression: str,
    identifiers: tuple[str, ...],
    operator: str,
    values: tuple[str, ...],
) -> None:
    analysis = analyze_filter(expression)

    assert analysis.errors == ()
    assert analysis.identifiers == identifiers
    assert analysis.predicates[0].operator == operator
    assert analysis.predicates[0].values == values
    assert analysis.tokens


def test_analyze_boolean_expression_and_quoted_identifiers() -> None:
    analysis = analyze_filter(
        "([Flow Regime] = 'Gravity' AND lifecycle_status <> 'Abandoned') OR \"override_flag\" = 1"
    )

    assert analysis.errors == ()
    assert analysis.identifiers == (
        "Flow Regime",
        "lifecycle_status",
        "override_flag",
    )
    assert [predicate.operator for predicate in analysis.predicates] == ["=", "<>", "="]


def test_analyze_not_between_and_escaped_string() -> None:
    analysis = analyze_filter("pressure_psi NOT BETWEEN 0 AND 20 AND owner = 'O''Brien Utilities'")

    assert analysis.errors == ()
    assert analysis.predicates[0].operator == "NOT BETWEEN"
    assert analysis.predicates[0].values == ("0", "20")
    assert analysis.predicates[1].values == ("O'Brien Utilities",)


@pytest.mark.parametrize(
    "expression",
    [
        "(network_role = 'Transmission'",
        "network_role = 'Transmission')",
        "network_role =",
        "network_role IN ()",
        "network_role = 'Transmission'; DROP TABLE assets",
        "network_role ~~ 'Transmission'",
        "",
    ],
)
def test_analyze_reports_invalid_or_unsupported_syntax(expression: str) -> None:
    analysis = analyze_filter(expression)

    assert analysis.errors


def test_partition_signature_is_limited_to_conjunctive_equality_constraints() -> None:
    partition = analyze_filter("network_role = 'Transmission' AND status IN ('Active', 'Planned')")
    disjunction = analyze_filter("network_role = 'Transmission' OR status = 'Active'")
    range_filter = analyze_filter("diameter_mm >= 600")

    assert partition.partition_signature == (
        ("network_role", ("Transmission",)),
        ("status", ("Active", "Planned")),
    )
    assert disjunction.partition_signature is None
    assert range_filter.partition_signature is None


def test_possible_overlap_proves_disjoint_simple_partitions() -> None:
    transmission = analyze_filter("network_role = 'Transmission'")
    distribution = analyze_filter("network_role = 'Distribution'")
    active_roles = analyze_filter("network_role IN ('Transmission', 'Distribution')")
    same = analyze_filter("network_role = 'Transmission'")

    assert possible_overlap(transmission, distribution) is False
    assert possible_overlap(transmission, active_roles) is True
    assert possible_overlap(transmission, same) is True


def test_possible_overlap_returns_unknown_for_complex_or_invalid_filters() -> None:
    simple = analyze_filter("network_role = 'Transmission'")
    disjunction = analyze_filter("network_role = 'Distribution' OR status = 'Active'")
    invalid = analyze_filter("network_role =")

    assert possible_overlap(simple, disjunction) is None
    assert possible_overlap(simple, invalid) is None
