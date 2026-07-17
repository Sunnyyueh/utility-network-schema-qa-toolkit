"""Canonical source-to-target mapping models."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import Field

from .common import SourceLocation, StrictModel


class EngineeringContext(StrictModel):
    network_role: str | None = None
    flow_regime: str | None = None
    geometry_type: str | None = None
    structure_type: str | None = None
    material: str | None = None
    lining: str | None = None
    coating: str | None = None
    nominal_diameter: float | None = None
    width: float | None = None
    height: float | None = None
    capacity: float | None = None
    pressure_class: str | None = None
    slope: float | None = None
    upstream_invert: float | None = None
    downstream_invert: float | None = None
    flow_direction: str | None = None
    installation_method: str | None = None
    installation_date: date | None = None
    lifecycle_status: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def value(self, field: str) -> Any:
        key = field.casefold()
        for model_field in type(self).model_fields:
            if model_field.casefold() == key and model_field != "extra":
                return getattr(self, model_field)
        for name, value in self.extra.items():
            if name.casefold() == key:
                return value
        return None


class FieldMapping(StrictModel):
    source_field: str | None = None
    target_field: str
    expression: str | None = None
    lookup: str | None = None
    default: Any = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class MappingPair(StrictModel):
    mapping_id: str
    source_dataset: str
    target_dataset: str
    definition_query: str | None = None
    purpose: str | None = None
    expected_count: int | None = Field(default=None, ge=0)
    selected_count: int | None = Field(default=None, ge=0)
    loaded_count: int | None = Field(default=None, ge=0)
    field_mappings: tuple[FieldMapping, ...] = ()
    asset_group: str | None = None
    asset_type: str | None = None
    rationale: str | None = None
    engineering_context: EngineeringContext | None = None
    enabled: bool = True
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DataReferenceEntry(StrictModel):
    source: str
    target: str
    mapping_workbook: str
    enabled: bool = True
    maintain_attachments: bool = True
    preserve_global_ids: bool = False
    definition_query: str | None = None
    mapping_id: str | None = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
