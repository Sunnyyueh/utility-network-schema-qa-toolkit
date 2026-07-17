"""Canonical schema, domain, and asset inventory models."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .common import SourceLocation, StrictModel


class FieldSchema(StrictModel):
    name: str
    data_type: str
    nullable: bool = True
    required: bool = False
    length: int | None = Field(default=None, ge=0)
    default: Any = None
    domain: str | None = None
    alias: str | None = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DatasetSchema(StrictModel):
    name: str
    geometry_type: str | None = None
    record_count: int | None = Field(default=None, ge=0)
    fields: tuple[FieldSchema, ...] = ()
    subtype_field: str | None = None
    asset_group_field: str | None = None
    asset_type_field: str | None = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_duplicate_fields(self) -> DatasetSchema:
        seen: set[str] = set()
        for item in self.fields:
            key = item.name.casefold()
            if key in seen:
                raise ValueError(f"duplicate field {item.name!r} in dataset {self.name!r}")
            seen.add(key)
        return self

    def field(self, name: str) -> FieldSchema | None:
        key = name.casefold()
        return next((item for item in self.fields if item.name.casefold() == key), None)


class DomainValue(StrictModel):
    code: str
    description: str
    target_code: str | None = None
    location: SourceLocation | None = None


class DomainSpec(StrictModel):
    name: str
    values: tuple[DomainValue, ...] = ()
    field_type: str | None = None
    location: SourceLocation | None = None

    def value(self, code: object) -> DomainValue | None:
        key = str(code).casefold()
        return next((item for item in self.values if item.code.casefold() == key), None)


class AssetTypeSpec(StrictModel):
    dataset: str
    asset_group: str
    asset_type: str
    asset_group_code: str | None = None
    asset_type_code: str | None = None
    categories: tuple[str, ...] = ()
    terminals: tuple[str, ...] = ()
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
