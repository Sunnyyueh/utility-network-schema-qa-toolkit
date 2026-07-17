from pathlib import Path

import pytest

from un_schema_qa.config import load_config
from un_schema_qa.engine import ValidatorRegistry, build_default_registry, run_validation
from un_schema_qa.exceptions import ValidationExecutionError
from un_schema_qa.models import (
    DatasetSchema,
    FieldSchema,
    Finding,
    ProjectData,
    Severity,
)
from un_schema_qa.validators import ValidationContext


class StubValidator:
    required_inputs: tuple[str, ...] = ()

    def __init__(self, name: str, findings: tuple[Finding, ...] = ()) -> None:
        self.name = name
        self.findings = findings

    def validate(self, context: ValidationContext) -> list[Finding]:
        assert context.project.name
        return list(self.findings)


class BrokenValidator(StubValidator):
    def validate(self, context: ValidationContext) -> list[Finding]:
        raise RuntimeError("validator exploded")


def valid_project() -> ProjectData:
    field = FieldSchema(name="id", data_type="integer")
    return ProjectData(
        name="engine",
        source_datasets=(DatasetSchema(name="Source", fields=(field,)),),
        target_datasets=(DatasetSchema(name="Target", fields=(field,)),),
    )


def finding(code: str = "TEST_DUPLICATE") -> Finding:
    return Finding(
        code=code,
        severity=Severity.WARNING,
        validator="stub",
        message="Test finding.",
        recommendation="Review the test.",
    )


def test_registry_preserves_order_and_rejects_duplicate_names() -> None:
    registry = ValidatorRegistry()
    registry.register(StubValidator("first"))
    registry.register(StubValidator("second"))

    assert registry.names == ("first", "second")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(StubValidator("FIRST"))


def test_default_registry_has_documented_order() -> None:
    assert build_default_registry().names == (
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


def test_engine_honors_explicit_checks_and_deduplicates_findings() -> None:
    duplicate = finding()
    registry = ValidatorRegistry(
        (StubValidator("first", (duplicate,)), StubValidator("second", (duplicate,)))
    )

    result = run_validation(valid_project(), checks=("second", "first"), registry=registry)

    assert result.validators == ("second", "first")
    assert len(result.findings) == 1
    assert result.summary.status == "warning"


def test_engine_skips_optional_empty_inventories() -> None:
    result = run_validation(valid_project())

    assert result.validators == (
        "schema",
        "mapping",
        "filters",
        "domains",
        "asset_classification",
    )


def test_engine_applies_severity_overrides(tmp_path: Path) -> None:
    for filename in ("source.csv", "target.csv", "mappings.csv"):
        (tmp_path / filename).write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "project.yml").write_text(
        """
project:
  name: override
inputs:
  source_schema: source.csv
  target_schema: target.csv
  mappings: mappings.csv
validation:
  enabled: [schema]
  severity_overrides:
    TEST_OVERRIDE: error
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path / "project.yml")
    registry = ValidatorRegistry((StubValidator("schema", (finding("TEST_OVERRIDE"),)),))

    result = run_validation(valid_project(), config=config, registry=registry)

    assert result.findings[0].severity == Severity.ERROR
    assert result.summary.status == "fail"


def test_input_fingerprint_is_stable_and_changes_with_project() -> None:
    first = run_validation(valid_project(), checks=("schema",))
    second = run_validation(valid_project(), checks=("schema",))
    changed = run_validation(
        valid_project().model_copy(update={"name": "changed"}), checks=("schema",)
    )

    assert first.input_fingerprint == second.input_fingerprint
    assert first.input_fingerprint != changed.input_fingerprint
    assert len(first.input_fingerprint) == 64


def test_validator_exception_is_wrapped_with_validator_name() -> None:
    registry = ValidatorRegistry((BrokenValidator("broken"),))

    with pytest.raises(ValidationExecutionError, match="broken"):
        run_validation(valid_project(), checks=("broken",), registry=registry)


def test_unknown_check_is_rejected() -> None:
    with pytest.raises(ValidationExecutionError, match="unknown validation check"):
        run_validation(valid_project(), checks=("missing",))
