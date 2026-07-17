"""Canonical validation and engineering rule models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .common import SourceLocation, StrictModel


class EngineeringCondition(StrictModel):
    field: str
    operator: str
    value: Any = None


class EngineeringRule(StrictModel):
    rule_id: str
    priority: int = 100
    match: Literal["all", "any"] = "all"
    conditions: tuple[EngineeringCondition, ...]
    target_asset_group: str
    target_asset_type: str
    explanation: str
    requires_review: bool = False
    location: SourceLocation | None = None


class AttributeRuleSpec(StrictModel):
    name: str
    dataset: str
    rule_type: str
    triggering_events: tuple[str, ...] = ()
    required_fields: tuple[str, ...] = ()
    domain_dependencies: tuple[str, ...] = ()
    expression: str | None = None
    location: SourceLocation | None = None


class NetworkRuleSpec(StrictModel):
    rule_type: str
    from_dataset: str
    from_asset_group: str
    from_asset_type: str
    to_dataset: str
    to_asset_group: str
    to_asset_type: str
    from_terminal: str | None = None
    to_terminal: str | None = None
    location: SourceLocation | None = None


class TerminalSpec(StrictModel):
    dataset: str
    asset_group: str
    asset_type: str
    terminal: str
    direction: str | None = None
    location: SourceLocation | None = None


class DirtyAreaRecord(StrictModel):
    dataset: str
    error_code: str
    global_id: str | None = None
    object_id: str | None = None
    message: str | None = None
    severity: str | None = None
    remediation_category: str | None = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
