# Input Formats

Tabular inputs may be CSV, TSV, JSON, YAML, XLSX, or XLSM. JSON/YAML may contain a list of row objects or an object with a `rows` list. Excel readers choose the sheet with the strongest unambiguous logical-column match.

Headers are case-insensitive and normalize spaces, dashes, punctuation, byte-order marks, and CamelCase. For example, `SourceDefinitionQuery`, `source_definition_query`, and `Definition Query` can resolve to the same logical concept where listed as aliases.

## Schema inventories

Required logical columns are `dataset`, `field`, and `data_type`. Common aliases include `feature_class`, `field_name`, and `field_type`. Optional columns include `geometry_type`, `record_count`, `nullable`, `required`, `length`, `default`, `domain`, `alias`, `subtype_field`, `asset_group_field`, and `asset_type_field`.

## Mapping inventory

Required row-level columns are `source_dataset` and `target_dataset`; field rows normally include `source_field` and `target_field`. Repeated `mapping_id` rows form one mapping.

Per-mapping audit columns include:

- `definition_query` (aliases `source_definition_query`, `filter`)
- `purpose`
- `expected_count`, `selected_count`, and `loaded_count`
- `asset_group`, `asset_type`, and `rationale`
- engineering context such as `network_role`, `flow_regime`, `geometry_type`, `structure_type`, material, dimensions, capacity, pressure class, slope, inverts, flow direction, installation, and lifecycle status

Definition Queries are source-side filters. This toolkit does not define a target-side Definition Query feature.

### Field-semantic mapping columns

Each field row may declare optional metadata for focused Utility Network mapping QA:

- `semantic_role`: `lifecycle_status`, `owner`, or `elevation`
- `field_rationale`: why the crosswalk, normalization, conversion, or review is appropriate
- `source_unit` and `target_unit`: required for `elevation`; supported canonical values are `m`, `ft`, and `us_survey_ft`, with common aliases
- `source_vertical_datum` and `target_vertical_datum`: required for `elevation` and compared case-insensitively after trimming
- `expression`: required when elevation units or vertical datums differ; retained as reviewable metadata and not executed

For `lifecycle_status`, assign source and target coded-value domains so the domain validator can review the explicit `target_code` crosswalk. For `owner`, use text fields and ensure the target length is not shorter; if either side uses a domain, both sides must use one. These checks inspect exported schemas and mapping metadata, not feature values.

## Domains and crosswalks

Domain rows use `domain`, `code`, and `description`. A source value may add `target_code` to document an explicit crosswalk. `field_type` is optional. Codes are treated as text for stable comparison.

## Other inventories

- Asset types: `dataset`, `asset_group`, `asset_type`, optional codes/categories/terminals.
- Data Reference: `source`, `target`, `mapping_workbook`, booleans, `definition_query`, `mapping_id`.
- Attribute rules: name, dataset, type, events, field/domain dependencies, expression.
- Network rules: type plus from/to dataset, asset group/type, and optional terminals.
- Terminals: dataset, asset group/type, terminal, optional direction.
- Dirty areas: dataset, error code, feature identifier, message, severity, remediation category.
- Engineering rules: YAML rule list described in [Validation Rules](validation-rules.md).

See the three projects under `examples/` for complete synthetic files.
