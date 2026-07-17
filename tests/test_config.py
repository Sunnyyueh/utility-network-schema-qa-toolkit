from pathlib import Path

import pytest

from un_schema_qa.config import DEFAULT_CHECKS, ProjectConfig, load_config
from un_schema_qa.exceptions import ConfigurationError
from un_schema_qa.models import Severity


def write_manifest(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "project.yml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_minimal_config_resolves_paths(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path,
        """
project:
  name: water-demo
inputs:
  source_schema: data/source.csv
  target_schema: data/target.csv
  mappings: data/mapping.csv
""",
    )

    config = load_config(manifest)

    assert isinstance(config, ProjectConfig)
    assert config.project.name == "water-demo"
    assert config.inputs.source_schema == tmp_path / "data/source.csv"
    assert config.validation.enabled == DEFAULT_CHECKS
    assert config.outputs.directory == tmp_path / "reports"
    assert config.outputs.formats == ("json", "csv", "markdown", "html")


def test_load_complete_config_preserves_policy(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path,
        """
project:
  name: sewer-demo
  profile: wastewater
inputs:
  source_schema: source.csv
  target_schema: target.xlsx
  mappings: mapping.yml
  dirty_areas: dirty.csv
validation:
  enabled: [schema, mapping, dirty_areas]
  fail_on: warning
  severity_overrides:
    MAP_TARGET_FIELD_UNKNOWN: warning
outputs:
  directory: artifacts
  formats: [json, html]
""",
    )

    config = load_config(manifest)

    assert config.project.profile == "wastewater"
    assert config.inputs.dirty_areas == tmp_path / "dirty.csv"
    assert config.validation.fail_on is Severity.WARNING
    assert config.validation.severity_overrides["MAP_TARGET_FIELD_UNKNOWN"] is Severity.WARNING
    assert config.outputs.formats == ("json", "html")


def test_unknown_config_keys_are_rejected(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path,
        """
project:
  name: typo-demo
  profille: water
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mapping.csv
""",
    )

    with pytest.raises(ConfigurationError, match="profille"):
        load_config(manifest)


def test_missing_or_invalid_manifest_is_contextual(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_config(tmp_path / "missing.yml")

    malformed = write_manifest(tmp_path, "project: [")
    with pytest.raises(ConfigurationError, match="cannot parse"):
        load_config(malformed)
