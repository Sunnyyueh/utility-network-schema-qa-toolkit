"""Convert heterogeneous tabular inputs into canonical project data."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .config import ProjectConfig
from .exceptions import InputFormatError
from .models import (
    AssetTypeSpec,
    AttributeRuleSpec,
    DataReferenceEntry,
    DatasetSchema,
    DirtyAreaRecord,
    DomainSpec,
    DomainValue,
    EngineeringContext,
    FieldMapping,
    FieldSchema,
    MappingPair,
    NetworkRuleSpec,
    ProjectData,
    SourceLocation,
    TerminalSpec,
)
from .normalization import (
    normalize_data_type,
    normalize_geometry_type,
    parse_bool,
    parse_float,
    parse_int,
    parse_list,
    resolve_columns,
)
from .readers import TabularRows, read_rows
from .row_schemas import (
    ASSET_COLUMNS,
    ATTRIBUTE_RULE_COLUMNS,
    DATA_REFERENCE_COLUMNS,
    DIRTY_AREA_COLUMNS,
    DOMAIN_COLUMNS,
    MAPPING_COLUMNS,
    NETWORK_RULE_COLUMNS,
    SCHEMA_COLUMNS,
    TERMINAL_COLUMNS,
)
from .workbooks import detect_sheet, inspect_workbook


def load_project_data(config: ProjectConfig) -> ProjectData:
    """Read every configured artifact into one canonical project model."""

    try:
        return ProjectData(
            name=config.project.name,
            profile=config.project.profile,
            source_datasets=_load_schemas(config.inputs.source_schema),
            target_datasets=_load_schemas(config.inputs.target_schema),
            source_domains=_optional(config.inputs.source_domains, DOMAIN_COLUMNS, _domains),
            target_domains=_optional(config.inputs.target_domains, DOMAIN_COLUMNS, _domains),
            mappings=_mappings(_read(config.inputs.mappings, MAPPING_COLUMNS)),
            asset_types=_optional(config.inputs.asset_types, ASSET_COLUMNS, _assets),
            data_reference=_optional(
                config.inputs.data_reference, DATA_REFERENCE_COLUMNS, _data_reference
            ),
            attribute_rules=_optional(
                config.inputs.attribute_rules, ATTRIBUTE_RULE_COLUMNS, _attribute_rules
            ),
            network_rules=_optional(
                config.inputs.network_rules, NETWORK_RULE_COLUMNS, _network_rules
            ),
            terminals=_optional(config.inputs.terminals, TERMINAL_COLUMNS, _terminals),
            dirty_areas=_optional(config.inputs.dirty_areas, DIRTY_AREA_COLUMNS, _dirty_areas),
        )
    except (ValidationError, ValueError) as error:
        raise InputFormatError(f"cannot build canonical project data: {error}") from error


def _read(path: Path, logical_schema: Mapping[str, set[str]]) -> TabularRows:
    if path.suffix.casefold() in {".xlsx", ".xlsm"}:
        inspection = inspect_workbook(path)
        sheet = detect_sheet(inspection, logical_schema)
        return read_rows(path, sheet=sheet)
    return read_rows(path)


def _optional(
    path: Path | None,
    schema: Mapping[str, set[str]],
    converter: Callable[[TabularRows], tuple[Any, ...]],
) -> tuple[Any, ...]:
    if path is None:
        return ()
    return converter(_read(path, schema))


def _columns(table: TabularRows, schema: Mapping[str, set[str]]) -> dict[str, str]:
    return resolve_columns(table.headers, schema)


def _value(row: Mapping[str, Any], columns: Mapping[str, str], name: str) -> Any:
    header = columns.get(name)
    return row.get(header) if header else None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _required(row: Mapping[str, Any], columns: Mapping[str, str], name: str) -> str:
    value = _text(_value(row, columns, name))
    if value is None:
        raise InputFormatError(f"required value {name!r} is missing")
    return value


def _extra(row: Mapping[str, Any], columns: Mapping[str, str]) -> dict[str, Any]:
    consumed = set(columns.values())
    return {
        key: value for key, value in row.items() if key not in consumed and value not in (None, "")
    }


def _load_schemas(path: Path) -> tuple[DatasetSchema, ...]:
    table = _read(path, SCHEMA_COLUMNS)
    columns = _columns(table, SCHEMA_COLUMNS)
    grouped: dict[str, list[tuple[dict[str, Any], SourceLocation]]] = defaultdict(list)
    display_names: dict[str, str] = {}
    for row, location in zip(table.rows, table.locations, strict=True):
        dataset_name = _required(row, columns, "dataset")
        key = dataset_name.casefold()
        display_names.setdefault(key, dataset_name)
        grouped[key].append((row, location))

    datasets: list[DatasetSchema] = []
    for key, records in grouped.items():
        first, location = records[0]
        fields: list[FieldSchema] = []
        for row, row_location in records:
            field_name = _required(row, columns, "field")
            nullable = parse_bool(_value(row, columns, "nullable"))
            required = parse_bool(_value(row, columns, "required"))
            fields.append(
                FieldSchema(
                    name=field_name,
                    data_type=normalize_data_type(_required(row, columns, "data_type")),
                    nullable=True if nullable is None else nullable,
                    required=False if required is None else required,
                    length=parse_int(_value(row, columns, "length")),
                    default=_value(row, columns, "default"),
                    domain=_text(_value(row, columns, "domain")),
                    alias=_text(_value(row, columns, "alias")),
                    location=row_location,
                    extra=_extra(row, columns),
                )
            )
        geometry = _text(_value(first, columns, "geometry_type"))
        datasets.append(
            DatasetSchema(
                name=display_names[key],
                geometry_type=normalize_geometry_type(geometry) if geometry else None,
                record_count=parse_int(_value(first, columns, "record_count")),
                fields=tuple(fields),
                subtype_field=_text(_value(first, columns, "subtype_field")),
                asset_group_field=_text(_value(first, columns, "asset_group_field")),
                asset_type_field=_text(_value(first, columns, "asset_type_field")),
                location=location,
            )
        )
    return tuple(datasets)


def _domains(table: TabularRows) -> tuple[DomainSpec, ...]:
    columns = _columns(table, DOMAIN_COLUMNS)
    grouped: dict[str, list[DomainValue]] = defaultdict(list)
    names: dict[str, str] = {}
    field_types: dict[str, str | None] = {}
    locations: dict[str, SourceLocation] = {}
    for row, location in zip(table.rows, table.locations, strict=True):
        name = _required(row, columns, "domain")
        key = name.casefold()
        names.setdefault(key, name)
        locations.setdefault(key, location)
        raw_type = _text(_value(row, columns, "field_type"))
        field_types.setdefault(key, normalize_data_type(raw_type) if raw_type else None)
        grouped[key].append(
            DomainValue(
                code=_required(row, columns, "code"),
                description=_required(row, columns, "description"),
                location=location,
            )
        )
    return tuple(
        DomainSpec(
            name=names[key],
            values=tuple(values),
            field_type=field_types[key],
            location=locations[key],
        )
        for key, values in grouped.items()
    )


def _mappings(table: TabularRows) -> tuple[MappingPair, ...]:
    columns = _columns(table, MAPPING_COLUMNS)
    grouped: dict[str, list[tuple[dict[str, Any], SourceLocation]]] = defaultdict(list)
    for row, location in zip(table.rows, table.locations, strict=True):
        source = _required(row, columns, "source_dataset")
        target = _required(row, columns, "target_dataset")
        mapping_id = _text(_value(row, columns, "mapping_id")) or f"{source}-to-{target}"
        grouped[mapping_id.casefold()].append((row, location))

    mappings: list[MappingPair] = []
    for records in grouped.values():
        first, location = records[0]
        source_dataset = _required(first, columns, "source_dataset")
        target_dataset = _required(first, columns, "target_dataset")
        resolved_mapping_id = _text(_first(records, columns, "mapping_id"))
        field_mappings: list[FieldMapping] = []
        for row, row_location in records:
            target_field = _text(_value(row, columns, "target_field"))
            if target_field:
                field_mappings.append(
                    FieldMapping(
                        source_field=_text(_value(row, columns, "source_field")),
                        target_field=target_field,
                        expression=_text(_value(row, columns, "expression")),
                        lookup=_text(_value(row, columns, "lookup")),
                        default=_value(row, columns, "default"),
                        location=row_location,
                    )
                )
        enabled = parse_bool(_first(records, columns, "enabled"))
        mappings.append(
            MappingPair(
                mapping_id=resolved_mapping_id or f"{source_dataset}-to-{target_dataset}",
                source_dataset=source_dataset,
                target_dataset=target_dataset,
                definition_query=_text(_first(records, columns, "definition_query")),
                purpose=_text(_first(records, columns, "purpose")),
                expected_count=parse_int(_first(records, columns, "expected_count")),
                field_mappings=tuple(field_mappings),
                asset_group=_text(_first(records, columns, "asset_group")),
                asset_type=_text(_first(records, columns, "asset_type")),
                rationale=_text(_first(records, columns, "rationale")),
                engineering_context=_engineering_context(records, columns),
                enabled=True if enabled is None else enabled,
                location=location,
            )
        )
    return tuple(mappings)


def _first(
    records: Sequence[tuple[Mapping[str, Any], SourceLocation]],
    columns: Mapping[str, str],
    name: str,
) -> Any:
    for row, _ in records:
        value = _value(row, columns, name)
        if value not in (None, ""):
            return value
    return None


def _engineering_context(
    records: Sequence[tuple[Mapping[str, Any], SourceLocation]],
    columns: Mapping[str, str],
) -> EngineeringContext | None:
    string_fields = (
        "network_role",
        "flow_regime",
        "material",
        "lining",
        "coating",
        "pressure_class",
        "flow_direction",
        "installation_method",
        "installation_date",
        "lifecycle_status",
    )
    number_fields = (
        "nominal_diameter",
        "width",
        "height",
        "capacity",
        "slope",
        "upstream_invert",
        "downstream_invert",
    )
    values: dict[str, Any] = {
        field: _text(_first(records, columns, field)) for field in string_fields
    }
    values.update({field: parse_float(_first(records, columns, field)) for field in number_fields})
    if not any(value is not None for value in values.values()):
        return None
    return EngineeringContext(**values)


def _assets(table: TabularRows) -> tuple[AssetTypeSpec, ...]:
    columns = _columns(table, ASSET_COLUMNS)
    return tuple(
        AssetTypeSpec(
            dataset=_required(row, columns, "dataset"),
            asset_group=_required(row, columns, "asset_group"),
            asset_type=_required(row, columns, "asset_type"),
            asset_group_code=_text(_value(row, columns, "asset_group_code")),
            asset_type_code=_text(_value(row, columns, "asset_type_code")),
            categories=parse_list(_value(row, columns, "categories")),
            terminals=parse_list(_value(row, columns, "terminals")),
            location=location,
            extra=_extra(row, columns),
        )
        for row, location in zip(table.rows, table.locations, strict=True)
    )


def _data_reference(table: TabularRows) -> tuple[DataReferenceEntry, ...]:
    columns = _columns(table, DATA_REFERENCE_COLUMNS)
    entries: list[DataReferenceEntry] = []
    for row, location in zip(table.rows, table.locations, strict=True):
        enabled = parse_bool(_value(row, columns, "enabled"))
        attachments = parse_bool(_value(row, columns, "maintain_attachments"))
        global_ids = parse_bool(_value(row, columns, "preserve_global_ids"))
        entries.append(
            DataReferenceEntry(
                source=_required(row, columns, "source"),
                target=_required(row, columns, "target"),
                mapping_workbook=_required(row, columns, "mapping_workbook"),
                enabled=True if enabled is None else enabled,
                maintain_attachments=True if attachments is None else attachments,
                preserve_global_ids=False if global_ids is None else global_ids,
                definition_query=_text(_value(row, columns, "definition_query")),
                mapping_id=_text(_value(row, columns, "mapping_id")),
                location=location,
                extra=_extra(row, columns),
            )
        )
    return tuple(entries)


def _attribute_rules(table: TabularRows) -> tuple[AttributeRuleSpec, ...]:
    columns = _columns(table, ATTRIBUTE_RULE_COLUMNS)
    return tuple(
        AttributeRuleSpec(
            name=_required(row, columns, "name"),
            dataset=_required(row, columns, "dataset"),
            rule_type=_required(row, columns, "rule_type"),
            triggering_events=parse_list(_value(row, columns, "triggering_events")),
            required_fields=parse_list(_value(row, columns, "required_fields")),
            domain_dependencies=parse_list(_value(row, columns, "domain_dependencies")),
            expression=_text(_value(row, columns, "expression")),
            location=location,
        )
        for row, location in zip(table.rows, table.locations, strict=True)
    )


def _network_rules(table: TabularRows) -> tuple[NetworkRuleSpec, ...]:
    columns = _columns(table, NETWORK_RULE_COLUMNS)
    return tuple(
        NetworkRuleSpec(
            rule_type=_required(row, columns, "rule_type"),
            from_dataset=_required(row, columns, "from_dataset"),
            from_asset_group=_required(row, columns, "from_asset_group"),
            from_asset_type=_required(row, columns, "from_asset_type"),
            to_dataset=_required(row, columns, "to_dataset"),
            to_asset_group=_required(row, columns, "to_asset_group"),
            to_asset_type=_required(row, columns, "to_asset_type"),
            from_terminal=_text(_value(row, columns, "from_terminal")),
            to_terminal=_text(_value(row, columns, "to_terminal")),
            location=location,
        )
        for row, location in zip(table.rows, table.locations, strict=True)
    )


def _terminals(table: TabularRows) -> tuple[TerminalSpec, ...]:
    columns = _columns(table, TERMINAL_COLUMNS)
    return tuple(
        TerminalSpec(
            dataset=_required(row, columns, "dataset"),
            asset_group=_required(row, columns, "asset_group"),
            asset_type=_required(row, columns, "asset_type"),
            terminal=_required(row, columns, "terminal"),
            direction=_text(_value(row, columns, "direction")),
            location=location,
        )
        for row, location in zip(table.rows, table.locations, strict=True)
    )


def _dirty_areas(table: TabularRows) -> tuple[DirtyAreaRecord, ...]:
    columns = _columns(table, DIRTY_AREA_COLUMNS)
    return tuple(
        DirtyAreaRecord(
            dataset=_required(row, columns, "dataset"),
            error_code=_required(row, columns, "error_code"),
            global_id=_text(_value(row, columns, "global_id")),
            object_id=_text(_value(row, columns, "object_id")),
            message=_text(_value(row, columns, "message")),
            severity=_text(_value(row, columns, "severity")),
            remediation_category=_text(_value(row, columns, "remediation_category")),
            location=location,
            extra=_extra(row, columns),
        )
        for row, location in zip(table.rows, table.locations, strict=True)
    )
