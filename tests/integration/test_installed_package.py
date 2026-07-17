from importlib.metadata import version
from pathlib import Path

from typer.testing import CliRunner

from un_schema_qa import __version__, load_project, validate_project, write_reports
from un_schema_qa.cli import app

ROOT = Path(__file__).parents[2]


def test_distribution_metadata_public_imports_and_console_commands() -> None:
    assert version("utility-network-schema-qa-toolkit") == __version__
    assert callable(load_project)
    assert callable(validate_project)
    assert callable(write_reports)

    runner = CliRunner()
    version_result = runner.invoke(app, ["version"])
    checks_result = runner.invoke(app, ["list-checks"])

    assert version_result.exit_code == 0
    assert __version__ in version_result.stdout
    assert checks_result.exit_code == 0
    assert "filters" in checks_result.stdout


def test_installed_surface_validates_example_and_renders_packaged_template(
    tmp_path: Path,
) -> None:
    result = validate_project(ROOT / "examples" / "water" / "project.yml")
    reports = write_reports(result, tmp_path, formats=("json", "html"))

    assert result.summary.status == "warning"
    assert reports["json"].is_file()
    assert reports["html"].read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
