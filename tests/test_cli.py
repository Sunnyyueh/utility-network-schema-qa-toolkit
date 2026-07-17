from pathlib import Path

from openpyxl import Workbook
from typer.testing import CliRunner

from un_schema_qa.cli import app
from un_schema_qa.version import __version__

runner = CliRunner()


def write_project(
    tmp_path: Path, *, mapping_target: str = "Target", filter_query: str = ""
) -> Path:
    (tmp_path / "source.csv").write_text(
        "dataset,field,data_type\nLegacy,id,integer\nLegacy,status,text\n",
        encoding="utf-8",
    )
    (tmp_path / "target.csv").write_text(
        "dataset,field,data_type\nTarget,id,integer\nTarget,status,text\n",
        encoding="utf-8",
    )
    query_columns = ",definition_query" if filter_query else ""
    query_values = f",{filter_query}" if filter_query else ""
    (tmp_path / "mappings.csv").write_text(
        "mapping_id,source_dataset,target_dataset,source_field,target_field"
        f"{query_columns}\nmain,Legacy,{mapping_target},id,id{query_values}\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "project.yml"
    manifest.write_text(
        """
project:
  name: cli-demo
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mappings.csv
validation:
  enabled: [schema, mapping, filters]
outputs:
  directory: configured-reports
  formats: [json]
""",
        encoding="utf-8",
    )
    return manifest


def test_cli_help_version_and_list_checks() -> None:
    help_result = runner.invoke(app, ["--help"])
    version_result = runner.invoke(app, ["version"])
    checks_result = runner.invoke(app, ["list-checks"])

    assert help_result.exit_code == 0
    assert "validate" in help_result.stdout
    assert version_result.exit_code == 0
    assert __version__ in version_result.stdout
    assert checks_result.exit_code == 0
    assert "asset_classification" in checks_result.stdout
    assert "definition" in checks_result.stdout.casefold()


def test_validate_writes_selected_formats_to_output_override(tmp_path: Path) -> None:
    manifest = write_project(tmp_path)
    output = tmp_path / "custom-reports"

    result = runner.invoke(
        app,
        [
            "validate",
            str(manifest),
            "--output",
            str(output),
            "--format",
            "json",
            "--format",
            "markdown",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "PASS" in result.stdout
    assert (output / "validation-report.json").is_file()
    assert (output / "validation-report.md").is_file()
    assert not (output / "validation-report.csv").exists()


def test_validate_exit_codes_for_warning_and_failure(tmp_path: Path) -> None:
    warning_dir = tmp_path / "warning"
    warning_dir.mkdir()
    warning_manifest = write_project(warning_dir, filter_query="status = 'Active'")
    fail_dir = tmp_path / "fail"
    fail_dir.mkdir()
    fail_manifest = write_project(fail_dir, mapping_target="MissingTarget")

    normal_warning = runner.invoke(app, ["validate", str(warning_manifest)])
    strict_warning = runner.invoke(app, ["validate", str(warning_manifest), "--fail-on-warning"])
    failed = runner.invoke(app, ["validate", str(fail_manifest)])

    assert normal_warning.exit_code == 0
    assert "WARNING" in normal_warning.stdout
    assert strict_warning.exit_code == 1
    assert failed.exit_code == 2
    assert "FAIL" in failed.stdout


def test_inspect_workbook_lists_sheet_headers_and_rows(tmp_path: Path) -> None:
    workbook_path = tmp_path / "mapping.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(["Source", "Target", "Definition Query"])
    sheet.append(["Legacy", "Target", "status = 'Active'"])
    workbook.save(workbook_path)

    result = runner.invoke(app, ["inspect-workbook", str(workbook_path)])

    assert result.exit_code == 0, result.output
    assert "Mappings" in result.stdout
    assert "Definition Query" in result.stdout
    assert "1 data row" in result.stdout


def test_init_creates_profile_project_and_protects_existing_files(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "starter"

    created = runner.invoke(app, ["init", str(destination), "--profile", "wastewater"])
    created_manifest = (destination / "project.yml").read_text()
    refused = runner.invoke(app, ["init", str(destination), "--profile", "water"])
    replaced = runner.invoke(app, ["init", str(destination), "--profile", "water", "--force"])

    assert created.exit_code == 0, created.output
    assert "profile: wastewater" in created_manifest
    assert (destination / "data" / "mappings.csv").is_file()
    assert refused.exit_code == 3
    assert "already exist" in refused.output
    assert replaced.exit_code == 0
    assert "profile: water" in (destination / "project.yml").read_text()


def test_typed_errors_are_concise_and_debug_prints_traceback(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"

    concise = runner.invoke(app, ["validate", str(missing)])
    debug = runner.invoke(app, ["validate", str(missing), "--debug"])

    assert concise.exit_code == 3
    assert "project manifest does not exist" in concise.output
    assert "Traceback" not in concise.output
    assert debug.exit_code == 3
    assert "Traceback" in debug.output
