from collections import Counter
from pathlib import Path

from un_schema_qa import validate_project, write_reports

EXAMPLE = Path(__file__).parents[2] / "examples" / "water" / "project.yml"


def test_water_example_is_a_complete_reviewable_warning_scenario(
    tmp_path: Path,
) -> None:
    result = validate_project(EXAMPLE)
    outputs = write_reports(result, tmp_path)

    assert result.summary.status == "warning"
    assert Counter(item.code for item in result.findings) == {
        "ASSET_RULE_MATCH": 2,
        "DIRTY_AREA_GROUP": 1,
    }
    assert result.validators == (
        "schema",
        "mapping",
        "filters",
        "domains",
        "asset_classification",
        "data_reference",
        "attribute_rules",
        "network_rules",
        "dirty_areas",
    )
    assert set(outputs) == {"json", "csv", "markdown", "html"}
    assert all(path.is_file() for path in outputs.values())
