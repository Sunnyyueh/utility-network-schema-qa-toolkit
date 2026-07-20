from un_schema_qa.models import FieldMapping


def test_field_mapping_stores_semantic_qa_metadata() -> None:
    mapping = FieldMapping(
        source_field="elevation_ft",
        target_field="elevation_m",
        semantic_role="elevation",
        source_unit="us_survey_ft",
        target_unit="m",
        source_vertical_datum="NAVD88",
        target_vertical_datum="NAVD88",
        field_rationale="Convert source survey feet to metres.",
    )

    assert mapping.semantic_role == "elevation"
    assert mapping.source_unit == "us_survey_ft"
    assert mapping.target_unit == "m"
    assert mapping.source_vertical_datum == "NAVD88"
    assert mapping.target_vertical_datum == "NAVD88"
    assert mapping.field_rationale == "Convert source survey feet to metres."


def test_field_mapping_semantic_qa_metadata_is_optional() -> None:
    mapping = FieldMapping(source_field="material", target_field="material")

    assert mapping.semantic_role is None
    assert mapping.source_unit is None
    assert mapping.target_unit is None
    assert mapping.source_vertical_datum is None
    assert mapping.target_vertical_datum is None
    assert mapping.field_rationale is None
