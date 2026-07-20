"""Production command-line interface for the toolkit."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from .api import validate_project
from .config import DEFAULT_CHECKS, load_config
from .exceptions import ConfigurationError, ToolkitError
from .reporters import write_reports
from .version import __version__
from .workbooks import inspect_workbook

app = typer.Typer(
    name="un-schema-qa",
    help="Validate Utility Network schema and migration QA artifacts.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


_CHECK_DESCRIPTIONS = {
    "schema": "Source and target field, type, geometry, and metadata consistency.",
    "mapping": "Dataset, field, required-target, type, lookup, and transform checks.",
    "field_semantics": "Lifecycle, owner, elevation unit, datum, and rationale checks.",
    "filters": "Source-side Definition Query syntax, fields, scope, counts, and overlap.",
    "domains": "Coded-value definitions, defaults, crosswalks, and asset codes.",
    "asset_classification": "Target inventory and explainable engineering rationale.",
    "data_reference": "Data Reference files, mapping IDs, datasets, and filter consistency.",
    "attribute_rules": "Declared attribute-rule fields, domains, triggers, and readiness.",
    "network_rules": "Declared asset endpoints, terminals, duplicates, and coverage.",
    "dirty_areas": "Exported issue identifiers, grouping, severity, and remediation.",
}


def _fail(error: Exception, *, debug: bool) -> NoReturn:
    typer.echo(f"Error: {error}", err=True)
    if debug:
        traceback.print_exc()
    raise typer.Exit(code=3)


@app.command("version")
def version_command() -> None:
    """Print the installed toolkit version."""

    typer.echo(f"un-schema-qa {__version__}")


@app.command("list-checks")
def list_checks() -> None:
    """List stable built-in validation check names."""

    for name in DEFAULT_CHECKS:
        typer.echo(f"{name:22} {_CHECK_DESCRIPTIONS[name]}")


@app.command("validate")
def validate_command(
    project: Annotated[Path, typer.Argument(help="Path to project.yml.")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Report output directory.")
    ] = None,
    formats: Annotated[
        list[str] | None,
        typer.Option("--format", "-f", help="Report format; repeat as needed."),
    ] = None,
    checks: Annotated[
        list[str] | None,
        typer.Option("--check", help="Validation check; repeat as needed."),
    ] = None,
    fail_on_warning: Annotated[
        bool,
        typer.Option("--fail-on-warning", help="Return exit code 1 for warnings."),
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Print tracebacks for runtime errors.")
    ] = False,
) -> None:
    """Validate one project and write selected reports."""

    try:
        config = load_config(project)
        result = validate_project(project, checks=checks or None)
        report_paths = write_reports(
            result,
            output or config.outputs.directory,
            formats=tuple(formats or config.outputs.formats),
        )
    except (ToolkitError, OSError, ValueError) as error:
        _fail(error, debug=debug)
    except Exception as error:  # pragma: no cover - defensive CLI boundary
        _fail(error, debug=debug)

    typer.echo(
        f"{result.summary.status.value.upper()}: {result.project_name} — "
        f"{result.summary.total} finding(s)"
    )
    for report_format, path in report_paths.items():
        typer.echo(f"  {report_format}: {path}")
    if result.summary.status.value == "fail":
        raise typer.Exit(code=2)
    if result.summary.status.value == "warning" and fail_on_warning:
        raise typer.Exit(code=1)


@app.command("inspect-workbook")
def inspect_workbook_command(
    workbook: Annotated[Path, typer.Argument(help="Excel workbook to inspect.")],
    debug: Annotated[
        bool, typer.Option("--debug", help="Print tracebacks for runtime errors.")
    ] = False,
) -> None:
    """List workbook sheets, headers, and non-empty data-row counts."""

    try:
        inspection = inspect_workbook(workbook)
    except (ToolkitError, OSError, ValueError) as error:
        _fail(error, debug=debug)
    typer.echo(f"Workbook: {inspection.path}")
    for sheet in inspection.sheets:
        row_label = "data row" if sheet.row_count == 1 else "data rows"
        typer.echo(f"- {sheet.name}: {sheet.row_count} {row_label}")
        typer.echo(f"  Headers: {', '.join(sheet.headers) or '(none)'}")


@app.command("init")
def init_command(
    directory: Annotated[Path, typer.Argument(help="Starter project directory.")],
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="Engineering profile: water, wastewater, or stormwater.",
        ),
    ] = "water",
    force: Annotated[
        bool, typer.Option("--force", help="Replace files created by this command.")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Print tracebacks for runtime errors.")
    ] = False,
) -> None:
    """Create a minimal runnable synthetic starter project."""

    try:
        _initialize_project(directory, profile=profile, force=force)
    except (ToolkitError, OSError, ValueError) as error:
        _fail(error, debug=debug)
    typer.echo(f"Created {profile.casefold()} starter project: {directory.resolve()}")


def _initialize_project(directory: Path, *, profile: str, force: bool) -> None:
    normalized_profile = profile.casefold()
    if normalized_profile not in {"water", "wastewater", "stormwater"}:
        raise ConfigurationError("profile must be water, wastewater, or stormwater")
    root = directory.expanduser().resolve()
    files = {
        root / "project.yml": _starter_manifest(normalized_profile),
        root / "data" / "source_schema.csv": _starter_source_schema(),
        root / "data" / "target_schema.csv": _starter_target_schema(),
        root / "data" / "mappings.csv": _starter_mapping(normalized_profile),
    }
    existing = [path for path in files if path.exists()]
    if existing and not force:
        names = ", ".join(str(path.relative_to(root)) for path in existing)
        raise ConfigurationError(f"starter files already exist: {names}")
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _starter_manifest(profile: str) -> str:
    return f"""project:
  name: {profile}-starter
  profile: {profile}
inputs:
  source_schema: data/source_schema.csv
  target_schema: data/target_schema.csv
  mappings: data/mappings.csv
validation:
  enabled: [schema, mapping, filters]
outputs:
  directory: reports
  formats: [json, markdown, html]
"""


def _starter_source_schema() -> str:
    return (
        "dataset,field,data_type,nullable\n"
        "LegacyLine,id,integer,false\n"
        "LegacyLine,network_role,text,false\n"
    )


def _starter_target_schema() -> str:
    return "dataset,field,data_type,nullable\nTargetLine,id,integer,false\n"


def _starter_mapping(profile: str) -> str:
    roles = {
        "water": "Distribution",
        "wastewater": "Gravity",
        "stormwater": "Conveyance",
    }
    role = roles[profile]
    return (
        "mapping_id,source_dataset,target_dataset,source_field,target_field,"
        "definition_query,purpose,expected_count\n"
        f"main,LegacyLine,TargetLine,id,id,network_role = '{role}',"
        f"Select reviewed {profile} line records,1\n"
    )


def main() -> None:
    """Console-script entry point."""

    app()


if __name__ == "__main__":  # pragma: no cover
    main()
