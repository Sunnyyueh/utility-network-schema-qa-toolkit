"""Shared validator contracts and finding helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from un_schema_qa.config import ProjectConfig
from un_schema_qa.models import Finding, ProjectData, Severity


@dataclass(frozen=True)
class ValidationContext:
    """Immutable inputs shared by every validator."""

    project: ProjectData
    config: ProjectConfig | None = None
    options: dict[str, Any] = field(default_factory=dict)


class Validator(Protocol):
    """Contract implemented by each validation component."""

    name: str
    required_inputs: tuple[str, ...]

    def validate(self, context: ValidationContext) -> list[Finding]: ...


def finding(
    code: str,
    severity: Severity,
    validator: str,
    message: str,
    recommendation: str,
    **context: Any,
) -> Finding:
    """Create a finding while keeping validator messages consistent."""

    return Finding(
        code=code,
        severity=severity,
        validator=validator,
        message=message,
        recommendation=recommendation,
        **context,
    )


_NUMERIC_TYPES = {"short", "integer", "float", "double"}
_DATE_TYPES = {"date", "datetime"}
_IDENTIFIER_TYPES = {"guid", "globalid"}


def types_compatible(source_type: str, target_type: str) -> bool:
    """Return conservative compatibility for normalized field types."""

    source = source_type.casefold()
    target = target_type.casefold()
    return (
        source == target
        or {source, target} <= _NUMERIC_TYPES
        or {source, target} <= _DATE_TYPES
        or {source, target} <= _IDENTIFIER_TYPES
    )
