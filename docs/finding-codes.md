# Finding Code Catalog

Codes are stable identifiers for automation and exact-code severity overrides. Messages may improve without changing code semantics.

## Schema

| Code | Meaning |
| --- | --- |
| `SCHEMA_DATASET_DUPLICATE` | A source or target dataset name repeats case-insensitively. |
| `SCHEMA_FIELD_DUPLICATE` | A dataset repeats a field name. |
| `SCHEMA_FIELDS_MISSING` | A dataset has no field inventory. |
| `SCHEMA_TYPE_UNSUPPORTED` | A field uses an unknown normalized type. |
| `SCHEMA_REQUIRED_NULLABLE` | Required and nullable metadata conflict. |
| `SCHEMA_DEFAULT_INVALID` | A default is incompatible with its field type. |
| `SCHEMA_GEOMETRY_MISMATCH` | Mapped datasets have different geometry types. |
| `SCHEMA_SUBTYPE_FIELD_UNKNOWN` | The subtype metadata references no field. |
| `SCHEMA_ASSET_GROUP_FIELD_UNKNOWN` | The asset-group metadata references no field. |
| `SCHEMA_ASSET_TYPE_FIELD_UNKNOWN` | The asset-type metadata references no field. |

## Mapping

| Code | Meaning |
| --- | --- |
| `MAP_DISABLED` | A mapping is intentionally disabled. |
| `MAP_SOURCE_DATASET_UNKNOWN` | Source dataset is absent from source schema. |
| `MAP_TARGET_DATASET_UNKNOWN` | Target dataset is absent from target schema. |
| `MAP_SOURCE_FIELD_UNKNOWN` | Source field is absent. |
| `MAP_TARGET_FIELD_UNKNOWN` | Target field is absent. |
| `MAP_TARGET_FIELD_DUPLICATE` | One target field is assigned more than once. |
| `MAP_REQUIRED_TARGET_UNMAPPED` | A required target has no mapping/default. |
| `MAP_TYPE_INCOMPATIBLE` | Direct source/target field types are incompatible. |
| `MAP_INPUT_MISSING` | Target mapping has no source, expression, or default. |
| `MAP_TRANSFORM_CONFLICT` | Expression and lookup are both declared. |
| `MAP_LOOKUP_UNKNOWN` | Lookup/domain name is not inventoried. |

## Field semantics

| Code | Default severity | Meaning |
| --- | --- | --- |
| `FIELD_SEMANTIC_ROLE_UNKNOWN` | `error` | A field row declares a semantic role other than lifecycle status, owner, or elevation. |
| `FIELD_SEMANTIC_RATIONALE_MISSING` | `warning` | A semantic field mapping lacks review rationale. |
| `FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING` | `error` | A lifecycle-status source field has no coded-value domain. |
| `FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING` | `error` | A lifecycle-status target field has no coded-value domain. |
| `FIELD_OWNER_TYPE_INVALID` | `error` | An owner source or target field is not text. |
| `FIELD_OWNER_LENGTH_RISK` | `warning` | Known owner source length exceeds target length and may truncate values. |
| `FIELD_OWNER_DOMAIN_ASYMMETRIC` | `error` | Only one side of an owner mapping declares a coded-value domain. |
| `FIELD_ELEVATION_TYPE_INVALID` | `error` | An elevation source or target field is not numeric. |
| `FIELD_ELEVATION_UNIT_MISSING` | `error` | Source or target elevation unit metadata is absent. |
| `FIELD_ELEVATION_UNIT_UNKNOWN` | `error` | A supplied elevation unit cannot be normalized to a supported unit. |
| `FIELD_ELEVATION_CONVERSION_MISSING` | `error` | Different elevation units have no conversion expression. |
| `FIELD_ELEVATION_DATUM_MISSING` | `error` | Source or target vertical datum metadata is absent. |
| `FIELD_ELEVATION_DATUM_TRANSFORM_MISSING` | `error` | Different vertical datums have no transformation expression. |

## Filters

| Code | Meaning |
| --- | --- |
| `FILTER_SYNTAX_INVALID` | Filter is outside the supported syntax subset. |
| `FILTER_FIELD_UNKNOWN` | Filter references an unknown source field. |
| `FILTER_PURPOSE_MISSING` | Filter scope lacks documentation. |
| `FILTER_EXPECTED_COUNT_MISSING` | Filter has no expected count baseline. |
| `FILTER_EMPTY_SELECTION` | Recorded selection count is zero. |
| `FILTER_EXPECTED_SELECTED_MISMATCH` | Expected and selected counts differ. |
| `FILTER_SELECTED_LOADED_MISMATCH` | Selected and loaded counts differ. |
| `FILTER_REQUIRED_FOR_PARTITION` | A shared source mapping has no per-item filter. |
| `FILTER_POSSIBLE_OVERLAP` | Simple partitions may select the same rows. |

## Domains and asset classification

| Code | Meaning |
| --- | --- |
| `DOMAIN_MISSING` | A field references an absent domain. |
| `DOMAIN_DUPLICATE` | Domain name repeats. |
| `DOMAIN_CODE_DUPLICATE` | Code repeats inside a domain. |
| `DOMAIN_DESCRIPTION_AMBIGUOUS` | Description is shared by distinct codes. |
| `DOMAIN_DEFAULT_INVALID` | Default is outside the assigned domain. |
| `DOMAIN_VALUE_UNMAPPED` | Source code has no direct or explicit target. |
| `DOMAIN_TARGET_CODE_UNKNOWN` | Explicit crosswalk points to an absent code. |
| `DOMAIN_ASSET_GROUP_CODE_INVALID` | Asset-group code is outside its domain. |
| `DOMAIN_ASSET_TYPE_CODE_INVALID` | Asset-type code is outside its domain. |
| `ASSET_CLASSIFICATION_INCOMPLETE` | Group/type pair is only partially supplied. |
| `ASSET_TYPE_UNKNOWN` | Selected group/type is outside inventory. |
| `ASSET_RATIONALE_MISSING` | Selected classification lacks rationale. |
| `ASSET_ENGINEERING_CONTEXT_MISSING` | Rules exist but context is absent. |
| `ASSET_RULE_NO_MATCH` | No engineering rule matched. |
| `ASSET_RULE_MATCH` | One or more explained same-target rules matched. |
| `ASSET_RULE_CONFLICT` | Matched rules recommend different targets. |
| `ASSET_RULE_DISAGREEMENT` | Mapping differs from every matched target. |

## Data Reference and declared rules

| Code | Meaning |
| --- | --- |
| `DATAREF_DISABLED` | Data Reference row is disabled. |
| `DATAREF_REQUIRED_VALUE_MISSING` | Source, target, or workbook is blank. |
| `DATAREF_DUPLICATE` | Enabled partition identity repeats. |
| `DATAREF_WORKBOOK_MISSING` | Referenced mapping workbook/file is absent. |
| `DATAREF_MAPPING_UNKNOWN` | Mapping ID is absent. |
| `DATAREF_MAPPING_DATASET_MISMATCH` | Row datasets disagree with mapping ID. |
| `DATAREF_FILTER_MISMATCH` | Row and mapping filters differ. |
| `ATTR_RULE_DUPLICATE` | Attribute-rule name repeats. |
| `ATTR_RULE_DATASET_UNKNOWN` | Rule target dataset is absent. |
| `ATTR_RULE_FIELD_UNKNOWN` | Required field is absent. |
| `ATTR_RULE_INPUT_UNMAPPED` | Required field lacks enabled mapping input. |
| `ATTR_RULE_DOMAIN_UNKNOWN` | Domain dependency is absent. |
| `ATTR_RULE_TYPE_UNSUPPORTED` | Rule type is outside the declared allowlist. |
| `ATTR_RULE_TRIGGER_INVALID` | Trigger is not insert/update/delete. |
| `ATTR_RULE_EXPRESSION_MISSING` | Expression text is missing for review. |
| `NETWORK_RULE_TYPE_UNSUPPORTED` | Network-rule type is unsupported. |
| `NETWORK_RULE_SELF_REFERENCE` | Both endpoints are identical. |
| `NETWORK_RULE_ASSET_UNKNOWN` | Endpoint asset classification is absent. |
| `NETWORK_RULE_TERMINAL_UNKNOWN` | Endpoint terminal is absent. |
| `NETWORK_RULE_DUPLICATE` | Exact rule repeats. |
| `NETWORK_RULE_REVERSE_DUPLICATE` | Connectivity endpoints repeat in reverse. |
| `NETWORK_RULE_MAPPING_UNCOVERED` | Mapped classification appears in no rule. |

## Dirty areas

| Code | Meaning |
| --- | --- |
| `DIRTY_AREA_IDENTIFIER_MISSING` | Exported issue has no feature identifier. |
| `DIRTY_AREA_SEVERITY_INVALID` | Severity is outside info/warning/error. |
| `DIRTY_AREA_CODE_UNKNOWN` | Code has no explicit remediation catalog/category. |
| `DIRTY_AREA_REMEDIATION_MISSING` | Group has no remediation category. |
| `DIRTY_AREA_GROUP` | Aggregated dataset/code/severity issue group. |
