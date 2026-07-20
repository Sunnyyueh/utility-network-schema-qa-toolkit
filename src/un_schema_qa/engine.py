"""Validation registry and deterministic orchestration."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence

from .config import DEFAULT_CHECKS, ProjectConfig
from .exceptions import ValidationExecutionError
from .models import Finding, ProjectData, ValidationResult
from .validators import (
    AssetClassificationValidator,
    AttributeRuleValidator,
    DataReferenceValidator,
    DirtyAreaValidator,
    DomainValidator,
    FieldSemanticsValidator,
    FilterValidator,
    MappingValidator,
    NetworkRuleValidator,
    SchemaValidator,
    ValidationContext,
    Validator,
)


class ValidatorRegistry:
    """Ordered collection of uniquely named validators."""

    def __init__(self, validators: Iterable[Validator] = ()) -> None:
        self._validators: dict[str, Validator] = {}
        for validator in validators:
            self.register(validator)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(validator.name for validator in self._validators.values())

    def register(self, validator: Validator) -> None:
        key = validator.name.casefold()
        if key in self._validators:
            raise ValueError(f"validator {validator.name!r} is already registered")
        self._validators[key] = validator

    def get(self, name: str) -> Validator | None:
        return self._validators.get(name.casefold())


def build_default_registry() -> ValidatorRegistry:
    """Create the stable built-in validator registry."""

    return ValidatorRegistry(
        (
            SchemaValidator(),
            MappingValidator(),
            FieldSemanticsValidator(),
            FilterValidator(),
            DomainValidator(),
            AssetClassificationValidator(),
            DataReferenceValidator(),
            AttributeRuleValidator(),
            NetworkRuleValidator(),
            DirtyAreaValidator(),
        )
    )


_OPTIONAL_INVENTORIES = {
    "data_reference": "data_reference",
    "attribute_rules": "attribute_rules",
    "network_rules": "network_rules",
    "dirty_areas": "dirty_areas",
}


def run_validation(
    project: ProjectData,
    *,
    config: ProjectConfig | None = None,
    checks: Sequence[str] | None = None,
    registry: ValidatorRegistry | None = None,
) -> ValidationResult:
    """Run selected validators and return one canonical immutable result."""

    active_registry = registry or build_default_registry()
    selected = tuple(
        checks if checks is not None else (config.validation.enabled if config else DEFAULT_CHECKS)
    )
    if len({name.casefold() for name in selected}) != len(selected):
        raise ValidationExecutionError("validation checks cannot be duplicated")
    unknown = [name for name in selected if active_registry.get(name) is None]
    if unknown:
        raise ValidationExecutionError(f"unknown validation check(s): {', '.join(unknown)}")

    context = ValidationContext(project=project, config=config)
    findings: list[Finding] = []
    executed: list[str] = []
    for name in selected:
        validator = active_registry.get(name)
        assert validator is not None
        inventory = _OPTIONAL_INVENTORIES.get(validator.name.casefold())
        if inventory and not getattr(project, inventory):
            continue
        try:
            validator_findings = validator.validate(context)
        except Exception as error:
            raise ValidationExecutionError(
                f"validator {validator.name!r} failed: {error}"
            ) from error
        findings.extend(validator_findings)
        executed.append(validator.name)

    if config and config.validation.severity_overrides:
        overrides = config.validation.severity_overrides
        findings = [
            item.model_copy(update={"severity": overrides[item.code]})
            if item.code in overrides
            else item
            for item in findings
        ]
    return ValidationResult.from_findings(
        project_name=project.name,
        input_fingerprint=_fingerprint(project, config),
        validators=executed,
        findings=findings,
    )


def _fingerprint(project: ProjectData, config: ProjectConfig | None) -> str:
    payload = {"project": project.model_dump(mode="json")}
    if config:
        payload["config"] = config.model_dump(mode="json")
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
