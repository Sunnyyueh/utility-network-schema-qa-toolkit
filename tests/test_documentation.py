import re
from pathlib import Path

from un_schema_qa.config import DEFAULT_CHECKS

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_required_user_and_technical_guides_exist() -> None:
    required = {
        "architecture.md",
        "configuration.md",
        "input-formats.md",
        "validation-rules.md",
        "finding-codes.md",
        "python-api.md",
        "cli.md",
        "report-schema.md",
    }

    assert required <= {path.name for path in DOCS.glob("*.md")}
    assert all(len(read(name).splitlines()) >= 20 for name in required)


def test_every_builtin_check_is_documented() -> None:
    documentation = read("validation-rules.md")

    assert all(f"`{name}`" in documentation for name in DEFAULT_CHECKS)


def test_every_finding_code_is_in_catalog() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src" / "un_schema_qa" / "validators").glob("*.py")
    )
    prefixes = "SCHEMA|MAP|FIELD|FILTER|DOMAIN|ASSET|DATAREF|ATTR_RULE|NETWORK_RULE|DIRTY_AREA"
    codes = set(re.findall(rf'"(({prefixes})_[A-Z0-9_]+)"', source))
    catalog = read("finding-codes.md")

    assert codes
    assert all(f"`{code}`" in catalog for code, _ in codes)


def test_semantic_field_mapping_input_is_documented() -> None:
    documentation = read("input-formats.md")

    assert all(
        f"`{name}`" in documentation
        for name in (
            "semantic_role",
            "source_unit",
            "target_unit",
            "source_vertical_datum",
            "target_vertical_datum",
            "field_rationale",
            "lifecycle_status",
            "owner",
            "elevation",
        )
    )


def test_every_cli_command_and_public_symbol_is_documented() -> None:
    cli_source = (ROOT / "src" / "un_schema_qa" / "cli.py").read_text(encoding="utf-8")
    commands = set(re.findall(r'@app\.command\("([a-z-]+)"\)', cli_source))
    cli_documentation = read("cli.md")
    api_documentation = read("python-api.md")

    assert commands == {"validate", "inspect-workbook", "init", "list-checks", "version"}
    assert all(f"`{command}`" in cli_documentation for command in commands)
    assert all(
        f"`{symbol}`" in api_documentation
        for symbol in ("load_project", "validate_project", "write_reports")
    )


def test_report_schema_guide_references_versioned_schema_and_formats() -> None:
    documentation = read("report-schema.md")

    assert "validation-report-v1.schema.json" in documentation
    assert all(f"`{name}`" in documentation for name in ("json", "csv", "markdown", "html"))


def test_v1_readme_and_governance_docs_are_release_ready() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = {
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "docs/tutorials/water.md",
        "docs/tutorials/wastewater.md",
        "docs/tutorials/stormwater.md",
    }

    assert all((ROOT / path).is_file() for path in required)
    assert "pip install utility-network-schema-qa-toolkit" in readme
    assert "V1.0" in readme
    assert all(path in readme for path in required)
    forbidden = (
        "planned toolkit",
        "final command names may change",
        "planning and initial documentation stage",
        "independent personal",
        "employer-owned",
        "public-safe",
        "private implementation",
        "company infrastructure",
    )
    assert not any(term in readme.casefold() for term in forbidden)


def test_readme_explains_semantic_field_mapping_workflow() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert all(
        f"`{name}`" in readme
        for name in (
            "semantic_role",
            "lifecycle_status",
            "owner",
            "elevation",
            "source_vertical_datum",
            "target_vertical_datum",
            "field_semantics",
        )
    )
    normalized = readme.casefold()
    assert "exported metadata" in normalized
    assert "feature records" in normalized
    assert "live utility network" in normalized


def test_all_local_readme_links_resolve() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"\[[^]]+\]\(([^)]+)\)", readme)
    local = [target.split("#", 1)[0] for target in links if "://" not in target]

    assert local
    assert all((ROOT / target).exists() for target in local if target)
