# Changelog

All notable changes are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Added

- Optional field-mapping metadata for explicit `lifecycle_status`, `owner`, and `elevation` semantic roles.
- Metadata-level checks for lifecycle domains, owner field compatibility, elevation units/conversions, vertical datums, and mapping rationale.
- A water example with lifecycle-domain crosswalks, owner normalization metadata, and US-survey-foot-to-metre elevation metadata.

### Documentation

- Clarified that manifests reference exported source/target metadata rather than feature records or live Utility Network connections.
- Added the semantic mapping columns, validator behavior, finding codes, limitations, and CLI workflow to the user guides.

## [1.0.0] - 2026-07-16

### Added

- Installable Python package and `un-schema-qa` CLI.
- CSV, TSV, JSON, YAML, XLSX, and XLSM readers with header aliases.
- Canonical schema, mapping, domain, asset, rule, dirty-area, finding, and result models.
- Schema, mapping, Definition Query, domain, asset-classification, Data Reference, attribute-rule, network-rule, terminal, and dirty-area validation.
- Safe non-executing filter tokenizer and conservative partition-overlap analysis.
- Explainable civil-engineering classification rules with deterministic operators and priority.
- Stable finding catalog, severity overrides, deterministic fingerprints, and pass/warning/fail summaries.
- JSON Schema-backed JSON, CSV, Markdown, and self-contained HTML reports.
- Synthetic water, wastewater, and stormwater projects with integration tests.
- User, technical, contributor, security, and release documentation.

[1.0.0]: https://github.com/Sunnyyueh/utility-network-schema-qa-toolkit/releases/tag/v1.0.0
