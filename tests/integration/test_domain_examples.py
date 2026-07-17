from collections import Counter
from pathlib import Path

from un_schema_qa import validate_project, write_reports

EXAMPLES = Path(__file__).parents[2] / "examples"


def test_wastewater_example_demonstrates_matches_and_rule_gap(
    tmp_path: Path,
) -> None:
    result = validate_project(EXAMPLES / "wastewater" / "project.yml")
    outputs = write_reports(result, tmp_path / "wastewater")

    assert result.summary.status == "warning"
    assert Counter(item.code for item in result.findings) == {
        "ASSET_RULE_MATCH": 2,
        "ASSET_RULE_NO_MATCH": 1,
    }
    assert set(outputs) == {"json", "csv", "markdown", "html"}


def test_stormwater_example_covers_asset_forms_and_dirty_area_groups(
    tmp_path: Path,
) -> None:
    result = validate_project(EXAMPLES / "stormwater" / "project.yml")
    outputs = write_reports(result, tmp_path / "stormwater")

    assert result.summary.status == "fail"
    assert Counter(item.code for item in result.findings) == {
        "ASSET_RULE_MATCH": 4,
        "DIRTY_AREA_GROUP": 2,
    }
    assert set(outputs) == {"json", "csv", "markdown", "html"}
