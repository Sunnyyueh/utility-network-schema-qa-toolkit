from pathlib import Path

import pytest
from openpyxl import Workbook

from un_schema_qa.exceptions import InputFormatError, WorkbookDetectionError
from un_schema_qa.readers import read_rows
from un_schema_qa.workbooks import detect_sheet, inspect_workbook


def save_workbook(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, rows in sheets.items():
        worksheet = workbook.create_sheet(name)
        for row in rows:
            worksheet.append(row)
    workbook.save(path)


def test_read_xlsx_sheet_preserves_headers_rows_and_locations(tmp_path: Path) -> None:
    path = tmp_path / "DataReference.xlsx"
    save_workbook(
        path,
        {
            "Notes": [["Instructions"], ["Review before loading"]],
            "Data Reference": [
                ["Source", "Target", "SourceDefinitionQuery"],
                ["LegacyLine", "WaterLine", "status = 'Active'"],
                [None, None, None],
            ],
        },
    )

    table = read_rows(path, sheet="Data Reference")

    assert table.headers == ("Source", "Target", "SourceDefinitionQuery")
    assert table.rows == (
        {
            "Source": "LegacyLine",
            "Target": "WaterLine",
            "SourceDefinitionQuery": "status = 'Active'",
        },
    )
    assert table.locations[0].sheet == "Data Reference"
    assert table.locations[0].row == 2


def test_inspect_and_detect_workbook_sheet(tmp_path: Path) -> None:
    path = tmp_path / "mapping.xlsx"
    save_workbook(
        path,
        {
            "Info": [["Description"], ["Synthetic example"]],
            "Mapping": [["Source", "Target", "MappingWorkbook"], ["A", "B", "map.xlsx"]],
        },
    )

    inspection = inspect_workbook(path)
    selected = detect_sheet(
        inspection,
        {
            "source": {"source"},
            "target": {"target"},
            "mapping_workbook": {"mapping_workbook"},
        },
    )

    assert inspection.sheets[1].name == "Mapping"
    assert inspection.sheets[1].row_count == 1
    assert selected == "Mapping"


def test_detect_sheet_reports_ambiguous_candidates(tmp_path: Path) -> None:
    path = tmp_path / "ambiguous.xlsx"
    rows = [["Source", "Target"], ["A", "B"]]
    save_workbook(path, {"Mapping 1": rows, "Mapping 2": rows})

    with pytest.raises(WorkbookDetectionError, match=r"Mapping 1.*Mapping 2"):
        detect_sheet(
            inspect_workbook(path),
            {"source": {"source"}, "target": {"target"}},
        )


def test_excel_reader_reports_missing_sheet_and_empty_workbook(tmp_path: Path) -> None:
    path = tmp_path / "empty.xlsx"
    save_workbook(path, {"Empty": []})

    with pytest.raises(InputFormatError, match=r"sheet.*Missing"):
        read_rows(path, sheet="Missing")
    with pytest.raises(InputFormatError, match="empty"):
        read_rows(path, sheet="Empty")
