import pytest

from un_schema_qa.exceptions import InputFormatError
from un_schema_qa.normalization import (
    normalize_data_type,
    normalize_geometry_type,
    normalize_header,
    parse_bool,
    parse_float,
    parse_int,
    parse_list,
    resolve_columns,
)
from un_schema_qa.row_schemas import MAPPING_COLUMNS


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SourceDefinitionQuery", "source_definition_query"),
        (" Target Field ", "target_field"),
        ("\ufeffAsset-Group Code", "asset_group_code"),
        ("OBJECTID", "objectid"),
    ],
)
def test_normalize_header(raw: str, expected: str) -> None:
    assert normalize_header(raw) == expected


def test_resolve_columns_recognizes_aliases_and_rejects_ambiguity() -> None:
    logical = {
        "source": {"source", "source_dataset"},
        "definition_query": {"definition_query", "source_definition_query"},
    }

    assert resolve_columns(["Source", "SourceDefinitionQuery"], logical) == {
        "source": "Source",
        "definition_query": "SourceDefinitionQuery",
    }

    with pytest.raises(InputFormatError, match="multiple columns"):
        resolve_columns(["Definition Query", "SourceDefinitionQuery"], logical)


def test_mapping_columns_recognize_semantic_qa_aliases() -> None:
    assert resolve_columns(
        [
            "QA Role",
            "From Unit",
            "To Unit",
            "Source Datum",
            "Target Datum",
            "Mapping Rationale",
        ],
        MAPPING_COLUMNS,
    ) == {
        "semantic_role": "QA Role",
        "source_unit": "From Unit",
        "target_unit": "To Unit",
        "source_vertical_datum": "Source Datum",
        "target_vertical_datum": "Target Datum",
        "field_rationale": "Mapping Rationale",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(True, True), ("YES", True), (1, True), ("false", False), (0, False), ("", None)],
)
def test_parse_bool(raw: object, expected: bool | None) -> None:
    assert parse_bool(raw) is expected


def test_parse_primitives_and_lists() -> None:
    assert parse_int("12") == 12
    assert parse_float("12.5") == 12.5
    assert parse_list("Main, Service; Hydrant") == ("Main", "Service", "Hydrant")
    assert parse_list(["Main", "Service"]) == ("Main", "Service")


def test_normalize_schema_types() -> None:
    assert normalize_data_type("String") == "text"
    assert normalize_data_type("esriFieldTypeDouble") == "double"
    assert normalize_data_type("Long Integer") == "integer"
    assert normalize_geometry_type("esriGeometryPolyline") == "polyline"
    assert normalize_geometry_type("Line") == "polyline"


def test_invalid_primitives_raise_contextual_errors() -> None:
    with pytest.raises(InputFormatError, match="boolean"):
        parse_bool("sometimes")
    with pytest.raises(InputFormatError, match="integer"):
        parse_int("12.5")
