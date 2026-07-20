"""Strict project manifest models and loading."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, ValidationError, field_validator

from .exceptions import ConfigurationError
from .models import Severity
from .models.common import StrictModel

DEFAULT_CHECKS = (
    "schema",
    "mapping",
    "field_semantics",
    "filters",
    "domains",
    "asset_classification",
    "data_reference",
    "attribute_rules",
    "network_rules",
    "dirty_areas",
)

ReportFormat = Literal["json", "csv", "markdown", "html"]


class ProjectMetadata(StrictModel):
    name: str
    profile: Literal["water", "wastewater", "stormwater"] | None = None


class InputConfig(StrictModel):
    source_schema: Path
    target_schema: Path
    mappings: Path
    source_domains: Path | None = None
    target_domains: Path | None = None
    asset_types: Path | None = None
    data_reference: Path | None = None
    attribute_rules: Path | None = None
    network_rules: Path | None = None
    terminals: Path | None = None
    dirty_areas: Path | None = None
    engineering_rules: Path | None = None


class ValidationConfig(StrictModel):
    enabled: tuple[str, ...] = DEFAULT_CHECKS
    fail_on: Severity = Severity.ERROR
    severity_overrides: dict[str, Severity] = Field(default_factory=dict)

    @field_validator("enabled")
    @classmethod
    def validate_checks(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        unknown = sorted(set(value) - set(DEFAULT_CHECKS))
        if unknown:
            raise ValueError(f"unknown validation checks: {', '.join(unknown)}")
        if len(value) != len(set(value)):
            raise ValueError("validation checks cannot be duplicated")
        return value

    @field_validator("severity_overrides")
    @classmethod
    def normalize_override_codes(cls, value: dict[str, Severity]) -> dict[str, Severity]:
        return {code.strip().upper(): severity for code, severity in value.items()}


class OutputConfig(StrictModel):
    directory: Path = Path("reports")
    formats: tuple[ReportFormat, ...] = ("json", "csv", "markdown", "html")

    @field_validator("formats")
    @classmethod
    def unique_formats(cls, value: tuple[ReportFormat, ...]) -> tuple[ReportFormat, ...]:
        if not value:
            raise ValueError("at least one report format is required")
        if len(value) != len(set(value)):
            raise ValueError("report formats cannot be duplicated")
        return value


class ProjectConfig(StrictModel):
    project: ProjectMetadata
    inputs: InputConfig
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)
    manifest_path: Path = Field(exclude=True)


def load_config(path: Path | str) -> ProjectConfig:
    """Load, validate, and resolve a project manifest."""

    manifest_path = Path(path).expanduser().resolve()
    if not manifest_path.is_file():
        raise ConfigurationError(f"project manifest does not exist: {manifest_path}")
    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ConfigurationError(
            f"cannot parse project manifest {manifest_path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise ConfigurationError(f"project manifest must contain a mapping: {manifest_path}")
    payload["manifest_path"] = manifest_path
    try:
        config = ProjectConfig.model_validate(payload)
    except ValidationError as error:
        raise ConfigurationError(f"invalid project manifest {manifest_path}: {error}") from error
    return _resolve_paths(config)


def _resolve_paths(config: ProjectConfig) -> ProjectConfig:
    base = config.manifest_path.parent

    def resolved(value: Path | None) -> Path | None:
        if value is None:
            return None
        return value if value.is_absolute() else (base / value).resolve()

    input_updates = {
        name: resolved(value)
        for name, value in config.inputs.model_dump().items()
        if isinstance(value, Path) or value is None
    }
    inputs = config.inputs.model_copy(update=input_updates)
    output_directory = resolved(config.outputs.directory)
    assert output_directory is not None
    outputs = config.outputs.model_copy(update={"directory": output_directory})
    return config.model_copy(update={"inputs": inputs, "outputs": outputs})
