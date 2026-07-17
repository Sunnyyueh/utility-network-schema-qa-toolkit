import json
from pathlib import Path

import pytest

from un_schema_qa.exceptions import InputFormatError
from un_schema_qa.readers import read_rows


def test_csv_reader_handles_bom_quoting_and_locations(tmp_path: Path) -> None:
    path = tmp_path / "mapping.csv"
    path.write_text(
        '\ufeffsource,target,purpose\nLegacyLine,WaterLine,"Map mains, not services"\n',
        encoding="utf-8",
    )

    table = read_rows(path)

    assert table.headers == ("source", "target", "purpose")
    assert table.rows[0]["purpose"] == "Map mains, not services"
    assert table.locations[0].path == str(path.resolve())
    assert table.locations[0].row == 2


def test_json_reader_accepts_row_arrays_and_keyed_objects(tmp_path: Path) -> None:
    array_path = tmp_path / "domains.json"
    array_path.write_text(
        json.dumps([{"domain": "Material", "code": "DI"}, {"domain": "Material", "code": "PVC"}]),
        encoding="utf-8",
    )
    keyed_path = tmp_path / "datasets.json"
    keyed_path.write_text(
        json.dumps({"WaterLine": {"geometry_type": "polyline"}}), encoding="utf-8"
    )

    array = read_rows(array_path)
    keyed = read_rows(keyed_path)

    assert len(array.rows) == 2
    assert keyed.rows == ({"identifier": "WaterLine", "geometry_type": "polyline"},)


def test_yaml_reader_accepts_rows_wrapper(tmp_path: Path) -> None:
    path = tmp_path / "rules.yml"
    path.write_text(
        """
rows:
  - rule_id: transmission
    priority: 10
  - rule_id: distribution
    priority: 20
""",
        encoding="utf-8",
    )

    table = read_rows(path)

    assert table.headers == ("rule_id", "priority")
    assert table.rows[1]["rule_id"] == "distribution"


@pytest.mark.parametrize("suffix", [".json", ".yml", ".csv"])
def test_empty_inputs_raise_contextual_error(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"empty{suffix}"
    path.write_text("", encoding="utf-8")

    with pytest.raises(InputFormatError, match="empty"):
        read_rows(path)


def test_reader_rejects_malformed_and_unsupported_files(tmp_path: Path) -> None:
    malformed = tmp_path / "bad.json"
    malformed.write_text("[{", encoding="utf-8")
    unsupported = tmp_path / "schema.txt"
    unsupported.write_text("dataset=WaterLine", encoding="utf-8")

    with pytest.raises(InputFormatError, match="cannot parse"):
        read_rows(malformed)
    with pytest.raises(InputFormatError, match="unsupported input format"):
        read_rows(unsupported)
