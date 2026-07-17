# Utility Network Schema QA Toolkit

`utility-network-schema-qa-toolkit` is an open-source Python toolkit for validating Utility Network schema mapping, data loading configuration, asset group/type alignment, attribute-rule readiness, dirty-area causes, and migration QA/QC reports.

The toolkit is designed as a foundational QA layer for Utility Network implementation and migration projects. Before a team can reliably migrate records between network models, it needs confidence that the target schema, source-to-target mapping, domains, asset classifications, data reference workbook, loading configuration, and validation rules are consistent and reviewable.

This repository is based on generalized Utility Network implementation concepts and public-safe examples only. It does not include client data, employer-owned materials, private schemas, internal URLs, credentials, internal scripts, confidential deliverables, or project-specific implementation details.

## Project Independence and Open-Source Scope

This is an independent personal open-source project. It is not an employer-owned product, client deliverable, or reproduction of any private implementation.

The project is inspired by public Utility Network concepts, public GIS data quality practices, open-source QA/QC patterns, and generalized professional experience with infrastructure data modernization. All examples, templates, test fixtures, and sample outputs should be created from synthetic data, public data, or generalized schemas that do not identify any client, employer, secured system, or confidential project.

The purpose of the project is to provide reusable open-source QA tooling for the broader GIS and utility community.

## Why This Toolkit Matters

Utility Network migration is not only a data-loading task. A migration can fail or produce unreliable results when the schema foundation is weak:

- Source fields may not map cleanly to target fields.
- Required target fields may be missing.
- Domain values may not match target coded values.
- Asset groups and asset types may be inconsistent.
- Attribute rules may depend on fields or values that are not loaded correctly.
- Connectivity, containment, association, or terminal rules may be incomplete.
- Dirty areas may appear without a clear error classification.
- Data Reference workbooks or loading configurations may contain stale paths, incomplete mappings, or incompatible field types.

This toolkit focuses on the validation layer that should happen before, during, and after Utility Network data loading.

## Use Cases

This toolkit can support:

- Utility Network schema readiness assessment.
- Source-to-target schema mapping validation.
- Field mapping completeness checks.
- Data type compatibility checks.
- Required field validation.
- Domain and coded-value validation.
- Asset group and asset type validation.
- Data Reference workbook or loading configuration validation.
- Attribute rule readiness checks.
- Connectivity, containment, association, and terminal rule review.
- Dirty-area classification and remediation reporting.
- Utility Network loading QA/QC reports.
- Pre-migration, post-load, and pre-acceptance validation workflows.

## What the Toolkit Can Do

The planned toolkit provides a repeatable QA workflow:

1. Read source schema metadata.
2. Read target Utility Network schema metadata.
3. Read a source-to-target mapping table or workbook.
4. Validate field mapping completeness.
5. Validate data type compatibility.
6. Validate required target fields.
7. Validate domains, subtypes, asset groups, and asset types.
8. Validate Data Reference workbook or loading configuration structure.
9. Review attribute-rule dependencies and readiness.
10. Review connectivity, containment, association, and terminal rule coverage.
11. Classify dirty-area or topology validation issues.
12. Generate QA/QC reports for analysts and project leads.

## Main Toolkit Input and Output

### Input

| Input | Required | Description |
| --- | --- | --- |
| Source schema inventory | Yes | Source layers, tables, fields, data types, domains, geometry types, and record counts. |
| Target Utility Network schema metadata | Yes | Target feature classes, fields, required fields, domains, subtypes, asset groups, asset types, tiers, terminals, and rule expectations. |
| Source-to-target mapping table | Yes | CSV, Excel, YAML, JSON, or other structured mapping between source schema and target schema. |
| Data Reference workbook or loading configuration | Recommended | Configuration used to guide data loading, including source datasets, target datasets, mapping references, filters, and loading rules. |
| Attribute rule inventory | Optional | Export or summary of attribute rules and their field/value dependencies. |
| Network rule inventory | Optional | Connectivity, containment, association, terminal, or subnetwork rule metadata. |
| Dirty-area or validation export | Optional | Dirty-area, topology, or validation issue export from a staging or Utility Network review environment. |
| QA configuration | Optional | YAML or JSON rules defining required checks, thresholds, severity levels, and reporting preferences. |

### Output

| Output | Description |
| --- | --- |
| Schema readiness report | Summary of target schema readiness and major blockers. |
| Mapping validation report | Missing mappings, duplicate mappings, incompatible fields, unmapped target fields, and data type issues. |
| Required field report | Required target fields that are missing, unmapped, or likely to be null after loading. |
| Domain validation report | Source values that do not map cleanly to target domains, subtypes, asset groups, or asset types. |
| Data Reference configuration report | Issues in loading configuration, stale references, missing targets, incomplete filters, or inconsistent mapping references. |
| Attribute rule readiness report | Attribute rules that may fail because of missing fields, missing values, unmapped domains, or incomplete dependencies. |
| Network rule coverage report | Connectivity, containment, association, terminal, or subnetwork rule gaps. |
| Dirty-area classification report | Dirty-area or topology validation issues grouped by likely cause and recommended remediation. |
| QA/QC summary | Pass/warning/fail summary by dataset, rule, severity, and recommended action. |
| Machine-readable report | JSON or CSV output for dashboards, audit trails, or automated review. |
| Human-readable report | Markdown or HTML report suitable for project documentation and stakeholder review. |

## Validator Modules

Planned package modules:

```text
un_schema_qa/
  io.py
  schema.py
  mapping.py
  domains.py
  asset_types.py
  data_reference.py
  attribute_rules.py
  network_rules.py
  dirty_areas.py
  validate.py
  report.py
  cli.py
```

## Example CLI Design

The final command names may change, but the toolkit is intended to work like this:

```bash
un-schema-qa validate-mapping \
  --source-schema examples/source_schema.csv \
  --target-schema examples/utility_network_schema.csv \
  --mapping examples/source_target_mapping.csv \
  --report outputs/mapping_validation_report.html
```

```bash
un-schema-qa validate-data-reference \
  --data-reference examples/data_reference.xlsx \
  --mapping examples/source_target_mapping.csv \
  --rules examples/qa_rules.yml \
  --report outputs/data_reference_validation_report.html
```

```bash
un-schema-qa validate-domains \
  --source-values examples/source_domain_values.csv \
  --target-domains examples/target_domains.csv \
  --mapping examples/domain_mapping.csv \
  --report outputs/domain_validation_report.html
```

```bash
un-schema-qa classify-dirty-areas \
  --dirty-areas examples/dirty_area_export.csv \
  --schema-report outputs/schema_readiness.json \
  --report outputs/dirty_area_classification.html
```

## Example QA Configuration

```yaml
checks:
  mapping:
    require_all_target_required_fields: true
    flag_duplicate_source_fields: true
    flag_unmapped_target_fields: true
    flag_data_type_mismatch: true
  domains:
    validate_coded_values: true
    validate_asset_groups: true
    validate_asset_types: true
    allow_unmapped_values: false
  data_reference:
    require_source_dataset: true
    require_target_dataset: true
    require_filter_documentation: true
  attribute_rules:
    check_required_fields: true
    check_domain_dependencies: true
  dirty_areas:
    classify_by_likely_cause: true
    group_by_dataset: true
outputs:
  formats:
    - html
    - json
    - csv
```

## Expected Results

A successful QA run should produce:

- A source-to-target mapping validation report.
- A required-field completeness report.
- A domain and asset-type compatibility report.
- A Data Reference workbook/configuration validation report.
- An attribute-rule readiness report.
- A network-rule coverage report.
- A dirty-area classification report, when dirty-area exports are provided.
- A final pass/warning/fail QA summary.

Expected practical benefits include:

- Earlier detection of schema and mapping problems.
- More consistent Utility Network loading configuration.
- Better documentation of source-to-target assumptions.
- Clearer dirty-area root-cause classification.
- Reduced rework during migration loading.
- More transparent QA/QC handoff between GIS analysts, developers, and project reviewers.

## Planned Python Package

The project is intended to be installable as a Python package:

```bash
pip install utility-network-schema-qa-toolkit
```

During early development, it may first be published to TestPyPI before release on PyPI.

## Roadmap

### Version 0.1.0

- Public README.
- Project structure.
- CLI skeleton.
- Source schema parser.
- Target schema parser.
- Source-to-target mapping validator.
- Required field checker.
- Basic Markdown/HTML report.

### Version 0.2.0

- Domain validation.
- Asset group/type validation.
- Data Reference workbook/configuration validation.
- JSON and CSV report outputs.
- Synthetic example schemas and mappings.

### Version 0.3.0

- Attribute rule readiness checks.
- Connectivity/containment/association rule coverage checks.
- Dirty-area classification.
- QA severity classification.

### Version 1.0.0

- Stable CLI and Python API.
- Full schema QA workflow.
- Public examples and tutorials.
- PyPI release suitable for external evaluation.

## Security and Confidentiality

This toolkit should never contain private client data, internal server paths, credentials, private schemas, screenshots of secured systems, confidential deliverables, or employer-owned implementation details.

Recommended practices:

- Use synthetic or public sample data.
- Replace organization names with generic placeholders.
- Avoid screenshots from private systems.
- Remove URLs, connection strings, usernames, tokens, and internal file paths.
- Do not commit private Data Reference workbooks or private schema exports.
- Review exported reports before publication.

## License

This project is planned for release under the MIT License.

## Intended Audience

- Utility Network implementation teams.
- Municipal GIS analysts.
- Water, wastewater, and stormwater GIS teams.
- GIS developers working with migration QA/QC.
- Civil and environmental engineering teams.
- Students and researchers studying geospatial infrastructure modernization.
- Open-source geospatial contributors.

## Project Status

Planning and initial documentation stage. The first implementation milestone is a Python package skeleton with schema parsers, mapping validation, Data Reference configuration checks, and a basic QA report generator.
