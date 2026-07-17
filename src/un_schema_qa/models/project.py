"""Aggregate canonical project data."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar

from pydantic import model_validator

from .common import StrictModel
from .mapping import DataReferenceEntry, MappingPair
from .rules import (
    AttributeRuleSpec,
    DirtyAreaRecord,
    EngineeringRule,
    NetworkRuleSpec,
    TerminalSpec,
)
from .schema import AssetTypeSpec, DatasetSchema, DomainSpec


class _Named(Protocol):
    name: str


NamedT = TypeVar("NamedT", bound=_Named)
ItemT = TypeVar("ItemT")


class ProjectData(StrictModel):
    name: str
    profile: str | None = None
    source_datasets: tuple[DatasetSchema, ...] = ()
    target_datasets: tuple[DatasetSchema, ...] = ()
    source_domains: tuple[DomainSpec, ...] = ()
    target_domains: tuple[DomainSpec, ...] = ()
    mappings: tuple[MappingPair, ...] = ()
    asset_types: tuple[AssetTypeSpec, ...] = ()
    data_reference: tuple[DataReferenceEntry, ...] = ()
    attribute_rules: tuple[AttributeRuleSpec, ...] = ()
    network_rules: tuple[NetworkRuleSpec, ...] = ()
    terminals: tuple[TerminalSpec, ...] = ()
    dirty_areas: tuple[DirtyAreaRecord, ...] = ()
    engineering_rules: tuple[EngineeringRule, ...] = ()

    @model_validator(mode="after")
    def reject_duplicate_collections(self) -> ProjectData:
        self._ensure_unique(self.source_datasets, "source dataset", lambda item: item.name)
        self._ensure_unique(self.target_datasets, "target dataset", lambda item: item.name)
        self._ensure_unique(self.source_domains, "source domain", lambda item: item.name)
        self._ensure_unique(self.target_domains, "target domain", lambda item: item.name)
        self._ensure_unique(self.mappings, "mapping", lambda item: item.mapping_id)
        return self

    @staticmethod
    def _ensure_unique(
        items: tuple[ItemT, ...], label: str, key_function: Callable[[ItemT], str]
    ) -> None:
        seen: set[str] = set()
        for item in items:
            value = key_function(item)
            normalized = value.casefold()
            if normalized in seen:
                raise ValueError(f"duplicate {label} {value!r}")
            seen.add(normalized)

    def source_dataset(self, name: str) -> DatasetSchema | None:
        return self._named(self.source_datasets, name)

    def target_dataset(self, name: str) -> DatasetSchema | None:
        return self._named(self.target_datasets, name)

    def source_domain(self, name: str) -> DomainSpec | None:
        return self._named(self.source_domains, name)

    def target_domain(self, name: str) -> DomainSpec | None:
        return self._named(self.target_domains, name)

    def asset_type(self, dataset: str, asset_group: str, asset_type: str) -> AssetTypeSpec | None:
        key = (dataset.casefold(), asset_group.casefold(), asset_type.casefold())
        return next(
            (
                item
                for item in self.asset_types
                if (
                    item.dataset.casefold(),
                    item.asset_group.casefold(),
                    item.asset_type.casefold(),
                )
                == key
            ),
            None,
        )

    @staticmethod
    def _named(items: tuple[NamedT, ...], name: str) -> NamedT | None:
        key = name.casefold()
        return next((item for item in items if item.name.casefold() == key), None)
