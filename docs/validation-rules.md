# Validation Rules

The default registry executes checks in the order below. Every validator is read-only and returns findings; it does not repair source files.

## `schema`

Checks duplicate datasets/fields, supported normalized types, empty field inventories, required/nullability conflicts, default compatibility, geometry compatibility for mapped datasets, and subtype/asset field references.

## `mapping`

Checks source and target datasets/fields, required target coverage, direct type compatibility, duplicate target assignments, missing inputs, conflicting expression/lookup paths, unknown lookups, and disabled mappings.

## `field_semantics`

Checks explicitly declared lifecycle status, owner, and elevation mapping roles. It reviews role support and field-level rationale without reading feature records or executing expressions. Role-specific domain, length, unit, conversion, and vertical datum checks are described below as they are enabled by mapping metadata.

## `filters`

Tokenizes a documented SQL-style subset without execution. It checks syntax, referenced source fields, purpose, expected scope, empty selections, expected-versus-selected and selected-versus-loaded counts, required filters for one-source-to-many partitions, and provable simple overlap risk. Complex overlap returns unknown rather than a false guarantee.

## `domains`

Checks missing/duplicate domains, duplicate codes, ambiguous descriptions, coded defaults, source-to-target code coverage, explicit `target_code` crosswalks, and asset group/type code membership.

## `asset_classification`

Checks complete asset group/type pairs, target inventory membership, rationale, and explainable engineering-rule results. It reports no match, one or more same-target matches, conflicts, and disagreement with the selected mapping. Rules never overwrite mappings.

Allowed engineering operators are `equals`, `not_equals`, `in`, `not_in`, `greater_than`, `greater_or_equal`, `less_than`, `less_or_equal`, `exists`, and `contains`. Rules use deterministic priority and `all` or `any` condition mode.

## `data_reference`

Checks required values, disabled rows, exact duplicate partitions, workbook existence, mapping ID, source/target consistency, and normalized Definition Query consistency.

## `attribute_rules`

Checks declared target datasets, field dependencies, enabled-mapping readiness, domain dependencies, supported rule types, triggers, duplicate names, and expression presence. Expressions are not executed.

## `network_rules`

Checks supported types, asset endpoints, terminal references, exact/reverse duplicates, self-reference, and coverage of mapped classifications. It does not build or trace network topology.

## `dirty_areas`

Checks feature identifiers and severity, then groups exported issues by dataset, error code, and severity with an explicit remediation category. It does not inspect a live topology.

Severity is `info`, `warning`, or `error`; aggregate status is `pass`, `warning`, or `fail`.
