from pathlib import Path

from un_schema_qa.config import load_config
from un_schema_qa.models import DataReferenceEntry, MappingPair, ProjectData
from un_schema_qa.validators import DataReferenceValidator, ValidationContext


def context(
    tmp_path: Path, entries: tuple[DataReferenceEntry, ...], mappings: tuple[MappingPair, ...]
) -> ValidationContext:
    for filename in ("source.csv", "target.csv", "mappings.csv"):
        (tmp_path / filename).write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "project.yml").write_text(
        """
project:
  name: references
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mappings.csv
""",
        encoding="utf-8",
    )
    return ValidationContext(
        project=ProjectData(name="references", data_reference=entries, mappings=mappings),
        config=load_config(tmp_path / "project.yml"),
    )


def entry(**updates: object) -> DataReferenceEntry:
    values = {
        "source": "LegacyLine",
        "target": "WaterLine",
        "mapping_workbook": "mapping.xlsx",
        "mapping_id": "water-main",
        "definition_query": "status = 'Active'",
    }
    values.update(updates)
    return DataReferenceEntry.model_validate(values)


def mapping(**updates: object) -> MappingPair:
    values = {
        "mapping_id": "water-main",
        "source_dataset": "LegacyLine",
        "target_dataset": "WaterLine",
        "definition_query": "status = 'Active'",
    }
    values.update(updates)
    return MappingPair.model_validate(values)


def codes(validation_context: ValidationContext) -> set[str]:
    return {item.code for item in DataReferenceValidator().validate(validation_context)}


def test_data_reference_reports_blank_required_values_and_disabled_rows(
    tmp_path: Path,
) -> None:
    invalid = entry(source="", target="", mapping_workbook="", enabled=False)

    assert {"DATAREF_REQUIRED_VALUE_MISSING", "DATAREF_DISABLED"} <= codes(
        context(tmp_path, (invalid,), (mapping(),))
    )


def test_data_reference_reports_duplicate_enabled_entries(tmp_path: Path) -> None:
    duplicate = entry()

    assert "DATAREF_DUPLICATE" in codes(
        context(tmp_path, (duplicate, duplicate.model_copy()), (mapping(),))
    )


def test_data_reference_reports_missing_mapping_workbook(tmp_path: Path) -> None:
    assert "DATAREF_WORKBOOK_MISSING" in codes(
        context(tmp_path, (entry(mapping_workbook="missing.xlsx"),), (mapping(),))
    )


def test_data_reference_reports_unknown_and_inconsistent_mapping_id(
    tmp_path: Path,
) -> None:
    unknown = entry(mapping_id="missing")
    mismatch = entry(target="SewerLine")

    assert "DATAREF_MAPPING_UNKNOWN" in codes(context(tmp_path, (unknown,), (mapping(),)))
    assert "DATAREF_MAPPING_DATASET_MISMATCH" in codes(context(tmp_path, (mismatch,), (mapping(),)))


def test_data_reference_reports_definition_query_mismatch(tmp_path: Path) -> None:
    inconsistent = entry(definition_query="status = 'Retired'")

    assert "DATAREF_FILTER_MISMATCH" in codes(context(tmp_path, (inconsistent,), (mapping(),)))


def test_data_reference_accepts_consistent_existing_workbook(tmp_path: Path) -> None:
    (tmp_path / "mapping.xlsx").write_bytes(b"workbook placeholder")

    assert DataReferenceValidator().validate(context(tmp_path, (entry(),), (mapping(),))) == []
