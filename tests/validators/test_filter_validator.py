from un_schema_qa.models import DatasetSchema, FieldSchema, MappingPair, ProjectData
from un_schema_qa.validators import FilterValidator, ValidationContext


def mapping(
    mapping_id: str,
    target: str,
    query: str | None,
    **updates: object,
) -> MappingPair:
    return MappingPair(
        mapping_id=mapping_id,
        source_dataset="LegacyLine",
        target_dataset=target,
        definition_query=query,
        **updates,
    )


def project(*mappings: MappingPair) -> ProjectData:
    return ProjectData(
        name="filters",
        source_datasets=(
            DatasetSchema(
                name="LegacyLine",
                fields=(
                    FieldSchema(name="network_role", data_type="text"),
                    FieldSchema(name="lifecycle_status", data_type="text"),
                ),
            ),
        ),
        target_datasets=tuple(
            DatasetSchema(name=name, fields=(FieldSchema(name="id", data_type="integer"),))
            for name in sorted({item.target_dataset for item in mappings})
        ),
        mappings=mappings,
    )


def findings(*mappings: MappingPair) -> list[object]:
    return FilterValidator().validate(ValidationContext(project=project(*mappings)))


def codes(*mappings: MappingPair) -> set[str]:
    return {item.code for item in findings(*mappings)}  # type: ignore[attr-defined]


def test_filter_validator_reports_syntax_and_unknown_fields() -> None:
    invalid = mapping(
        "invalid",
        "WaterLine",
        "missing_field = 'value' AND (network_role =",
        purpose="Select invalid test rows.",
    )

    assert {"FILTER_SYNTAX_INVALID", "FILTER_FIELD_UNKNOWN"} <= codes(invalid)


def test_filter_validator_requires_documentation_and_expected_scope() -> None:
    undocumented = mapping("undocumented", "WaterLine", "network_role = 'Transmission'")

    assert {"FILTER_PURPOSE_MISSING", "FILTER_EXPECTED_COUNT_MISSING"} <= codes(undocumented)


def test_filter_validator_compares_expected_selected_and_loaded_counts() -> None:
    count_mismatch = mapping(
        "counts",
        "WaterLine",
        "network_role = 'Transmission'",
        purpose="Select transmission mains.",
        expected_count=10,
        selected_count=8,
        loaded_count=7,
    )

    assert {
        "FILTER_EXPECTED_SELECTED_MISMATCH",
        "FILTER_SELECTED_LOADED_MISMATCH",
    } <= codes(count_mismatch)


def test_filter_validator_reports_empty_selection() -> None:
    empty = mapping(
        "empty",
        "WaterLine",
        "network_role = 'Transmission'",
        purpose="Select transmission mains.",
        expected_count=10,
        selected_count=0,
        loaded_count=0,
    )

    assert "FILTER_EMPTY_SELECTION" in codes(empty)


def test_partitioned_source_requires_per_mapping_filters() -> None:
    transmission = mapping(
        "transmission",
        "TransmissionLine",
        "network_role = 'Transmission'",
        purpose="Select transmission mains.",
        expected_count=4,
    )
    distribution = mapping("distribution", "DistributionLine", None)

    assert "FILTER_REQUIRED_FOR_PARTITION" in codes(transmission, distribution)


def test_filter_validator_reports_possible_overlap_but_not_disjoint_partitions() -> None:
    broad = mapping(
        "broad",
        "AllMain",
        "network_role IN ('Transmission', 'Distribution')",
        purpose="Select all mains.",
        expected_count=10,
    )
    transmission = mapping(
        "transmission",
        "TransmissionLine",
        "network_role = 'Transmission'",
        purpose="Select transmission mains.",
        expected_count=4,
    )
    distribution = mapping(
        "distribution",
        "DistributionLine",
        "network_role = 'Distribution'",
        purpose="Select distribution mains.",
        expected_count=6,
    )

    assert "FILTER_POSSIBLE_OVERLAP" in codes(broad, transmission)
    assert "FILTER_POSSIBLE_OVERLAP" not in codes(transmission, distribution)


def test_filter_validator_accepts_documented_single_mapping_filter() -> None:
    valid = mapping(
        "valid",
        "WaterLine",
        "network_role = 'Transmission' AND lifecycle_status <> 'Abandoned'",
        purpose="Select active transmission mains.",
        expected_count=10,
        selected_count=10,
        loaded_count=10,
    )

    assert FilterValidator().validate(ValidationContext(project=project(valid))) == []
