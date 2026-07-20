# Field Mapping Semantic QA Design

## Goal

Extend the toolkit's metadata-only source-to-target field mapping review with explicit Utility Network semantic roles for lifecycle status, owner, and elevation. The checks must remain deterministic, license-free, offline, and safe for exported metadata artifacts.

## Scope

The change adds optional metadata to individual field mapping rows, a built-in `field_semantics` validator, runnable synthetic water examples, finding documentation, and README guidance.

The validator reviews mapping design. It does not read feature records, execute mapping expressions, connect to a geodatabase or service, validate coordinate operations, or decide whether an owner or lifecycle value is correct for a particular asset.

## Input Contract

Mapping inventories accept these optional field-row columns:

| Logical column | Purpose |
| --- | --- |
| `semantic_role` | Declares `lifecycle_status`, `owner`, or `elevation`. |
| `source_unit` | Declares the source elevation unit. |
| `target_unit` | Declares the target elevation unit. |
| `source_vertical_datum` | Declares the source elevation vertical datum. |
| `target_vertical_datum` | Declares the target elevation vertical datum. |
| `field_rationale` | Documents normalization, conversion, or review intent. |

Headers remain case-insensitive and use the toolkit's existing alias resolution. Initial aliases include `qa_role` and `field_role` for `semantic_role`, `from_unit` and `to_unit` for units, `source_datum` and `target_datum` for vertical datums, and `mapping_rationale` for `field_rationale`.

Semantic roles are explicit. The toolkit does not infer a role from field names such as `status`, `owner_id`, `z`, or `invert` because those names are project-dependent and ambiguous.

The canonical `FieldMapping` model stores the six new values. They participate in project fingerprints and all supported mapping readers through the existing canonical loader.

## Validator Registration

`FieldSemanticsValidator` has the stable name `field_semantics`. It is registered after `mapping` and before `filters`, included in `DEFAULT_CHECKS`, displayed by `un-schema-qa list-checks`, and available in manifest `validation.enabled` lists.

The validator requires mappings plus source and target schema inventories. It skips field rows without `semantic_role`, allowing existing projects to continue unchanged.

## Shared Validation

For every declared semantic role, the validator first resolves the source and target datasets and fields. The existing mapping validator remains authoritative for missing datasets, missing fields, missing inputs, duplicate target assignments, and general type compatibility. Semantic checks do not duplicate those findings.

An unsupported non-empty role produces `FIELD_SEMANTIC_ROLE_UNKNOWN` at error severity. A supported role without `field_rationale` produces `FIELD_SEMANTIC_RATIONALE_MISSING` at warning severity. Role comparison is case-insensitive and accepts spaces or hyphens after header-style normalization.

## Lifecycle Status QA

Lifecycle status mappings require coded-value semantics on both sides:

- A source field without a source domain produces `FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING` at error severity.
- A target field without a target domain produces `FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING` at error severity.
- Existing domain validation remains responsible for missing domain inventories, invalid defaults, incomplete direct matches, and invalid `target_code` crosswalk targets.

This division prevents duplicate crosswalk findings while adding a clear role-specific requirement that lifecycle status not be treated as undocumented free text.

## Owner QA

Owner mappings support direct text mapping, lookup/expression normalization, or coded-value domains:

- Source and target fields must be text. A non-text side produces `FIELD_OWNER_TYPE_INVALID` at error severity.
- When both text lengths are known and the source length exceeds the target length, `FIELD_OWNER_LENGTH_RISK` is emitted at warning severity.
- If either side uses a domain, both sides must use domains so the existing crosswalk validator can evaluate the mapping. A one-sided domain produces `FIELD_OWNER_DOMAIN_ASYMMETRIC` at error severity.
- A mapping using `lookup` or `expression` relies on the shared `field_rationale` requirement to document the normalization intent.

The validator does not inspect organization names or execute a normalization expression.

## Elevation QA

Elevation mappings require numeric schema types and explicit vertical reference metadata:

- A source or target type outside `small_integer`, `integer`, `float`, and `double` produces `FIELD_ELEVATION_TYPE_INVALID` at error severity.
- Missing source or target unit produces `FIELD_ELEVATION_UNIT_MISSING` at error severity.
- Supported canonical units are `m`, `ft`, and `us_survey_ft`. Common aliases normalize to those values. An unsupported supplied unit produces `FIELD_ELEVATION_UNIT_UNKNOWN` at error severity.
- Different canonical units without `expression` produce `FIELD_ELEVATION_CONVERSION_MISSING` at error severity.
- Missing source or target vertical datum produces `FIELD_ELEVATION_DATUM_MISSING` at error severity.
- Different non-empty datum names without `expression` produce `FIELD_ELEVATION_DATUM_TRANSFORM_MISSING` at error severity.

Datum comparison is trimmed and case-insensitive but otherwise exact. The toolkit records whether a transformation is declared; it does not execute the expression or validate a coordinate operation.

## Findings and Reports

All new findings use the existing `Finding` model and report writers. Each finding includes the mapping ID, target dataset, target field, source location when available, a direct explanation, and a remediation recommendation. No reporter schema changes are required.

The finding catalog documents every new code and default severity. Exact-code severity overrides continue to work through the existing manifest configuration.

## Synthetic Water Example

The water example will include:

- lifecycle status fields with source and target coded-value domains and explicit `target_code` crosswalks;
- owner text fields whose target length is sufficient, with a documented normalization rationale; and
- elevation numeric fields using metres and NAVD88 on both sides.

The example mapping remains warning-free except for its existing intentional informational findings. Integration tests confirm that the `field_semantics` validator executes and that the example produces no semantic error.

Targeted unit tests separately cover every failure code, case-insensitive role handling, unit aliases, direct same-unit elevation mapping, required conversions, datum differences, domain asymmetry, and owner length risk.

## README and Supporting Documentation

The README will explain that a project manifest points to metadata exported from real source and target environments rather than feature-level records. It will show a complete manifest fragment, mapping CSV rows for the three roles, the QA applied to each role, CLI commands, expected finding behavior, and explicit limitations.

`docs/input-formats.md`, `docs/validation-rules.md`, `docs/finding-codes.md`, `docs/configuration.md`, and `CHANGELOG.md` will remain consistent with the implementation.

## Compatibility and Release Posture

All new mapping columns are optional, so existing mapping files remain valid. Adding `field_semantics` to default checks does not create findings for mappings without semantic roles. The work is additive and does not change the current package version or publish a release; versioning and PyPI publication require a separate release decision after the feature is merged.

## Commit Strategy

Implementation will use at least ten substantive commits. Each implementation commit will leave the branch testable and will group one reviewable concern: canonical metadata, aliases/loading, registry wiring, lifecycle checks, owner checks, elevation checks, synthetic examples, finding/reference documentation, README usage, and changelog/final integration. Empty commits will not be used.
