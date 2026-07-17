from un_schema_qa.models import DirtyAreaRecord, ProjectData
from un_schema_qa.validators import DirtyAreaValidator, ValidationContext


def issue(**updates: object) -> DirtyAreaRecord:
    values = {
        "dataset": "WaterLine",
        "error_code": "25",
        "global_id": "{ABC}",
        "message": "Invalid geometry",
        "severity": "error",
    }
    values.update(updates)
    return DirtyAreaRecord.model_validate(values)


def validate(*issues: DirtyAreaRecord, catalog: dict[str, str] | None = None) -> list[object]:
    return DirtyAreaValidator().validate(
        ValidationContext(
            project=ProjectData(name="dirty", dirty_areas=issues),
            options={"dirty_area_remediation": catalog or {}},
        )
    )


def codes(*issues: DirtyAreaRecord, catalog: dict[str, str] | None = None) -> set[str]:
    return {item.code for item in validate(*issues, catalog=catalog)}  # type: ignore[attr-defined]


def test_dirty_area_reports_missing_feature_identifier() -> None:
    assert "DIRTY_AREA_IDENTIFIER_MISSING" in codes(issue(global_id=None, object_id=None))


def test_dirty_area_reports_unknown_code_and_missing_remediation() -> None:
    assert {"DIRTY_AREA_CODE_UNKNOWN", "DIRTY_AREA_REMEDIATION_MISSING"} <= codes(
        issue(error_code="999")
    )


def test_dirty_area_groups_matching_issues_with_count_and_category() -> None:
    results = validate(
        issue(global_id="{A}"),
        issue(global_id="{B}"),
        catalog={"25": "geometry"},
    )
    groups = [item for item in results if item.code == "DIRTY_AREA_GROUP"]  # type: ignore[attr-defined]

    assert len(groups) == 1
    assert groups[0].details["count"] == 2  # type: ignore[attr-defined]
    assert groups[0].details["remediation_category"] == "geometry"  # type: ignore[attr-defined]


def test_dirty_area_record_category_overrides_catalog() -> None:
    results = validate(
        issue(remediation_category="survey-review"),
        catalog={"25": "geometry"},
    )
    group = next(item for item in results if item.code == "DIRTY_AREA_GROUP")  # type: ignore[attr-defined]

    assert group.details["remediation_category"] == "survey-review"  # type: ignore[attr-defined]


def test_dirty_area_reports_invalid_severity() -> None:
    assert "DIRTY_AREA_SEVERITY_INVALID" in codes(issue(severity="urgent"))
