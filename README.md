# Utility Network Schema QA Toolkit

`utility-network-schema-qa-toolkit` is an open-source Python toolkit for validating Utility Network schema mapping, data loading configuration, asset group/type alignment, attribute-rule readiness, dirty-area causes, and migration QA/QC reports.

The toolkit is designed as a foundational QA layer for Utility Network implementation and migration projects. Before a team can reliably migrate records between network models, it needs confidence that the target schema, source-to-target mapping, domains, asset classifications, data reference workbook, loading configuration, and validation rules are consistent and reviewable.

## Why This Toolkit Matters

Utility Network migration is not only a data-loading task. A migration can fail or produce unreliable results when the schema foundation is weak:

- Source fields may not map cleanly to target fields.
- A single source dataset may need separate filters to route different records to different target classifications.
- Required target fields may be missing.
- Domain values may not match target coded values.
- Asset groups and asset types may be inconsistent.
- Engineering attributes needed to support an asset classification may be incomplete or contradictory.
- Attribute rules may depend on fields or values that are not loaded correctly.
- Connectivity, containment, association, or terminal rules may be incomplete.
- Dirty areas may appear without a clear error classification.
- Data Reference workbooks or loading configurations may contain stale paths, incomplete mappings, or incompatible field types.

This toolkit focuses on the validation layer that should happen before, during, and after Utility Network data loading.

## Use Cases

This toolkit can support:

- Utility Network schema readiness assessment.
- Source-to-target schema mapping validation.
- Per-mapping Definition Query and filter documentation.
- Filter field, overlap, empty-selection, and record-count checks.
- Field mapping completeness checks.
- Data type compatibility checks.
- Required field validation.
- Domain and coded-value validation.
- Asset group and asset type validation.
- Civil-engineering-informed asset group and asset type review.
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
4. Read the Definition Query or filter assigned to each source-to-target mapping.
5. Validate field mapping completeness.
6. Validate data type compatibility.
7. Validate required target fields.
8. Review filter fields, selection scope, overlapping filters, and selected record counts.
9. Validate domains, subtypes, asset groups, and asset types.
10. Review civil engineering context used to support asset classifications.
11. Validate Data Reference workbook or loading configuration structure.
12. Review attribute-rule dependencies and readiness.
13. Review connectivity, containment, association, and terminal rule coverage.
14. Classify dirty-area or topology validation issues.
15. Generate QA/QC reports for analysts and project leads.

## Per-Mapping Definition Queries and Filters

Each source-to-target mapping can include its own SQL-style Definition Query or filter. The filter defines which source records belong to that mapping pair, allowing one source dataset to be divided across multiple target datasets, asset groups, or asset types without treating every source record the same way.

Document the filter together with the source, target, mapping purpose, and expected record scope. For example:

| Source dataset | Target classification | Definition Query or filter | Purpose |
| --- | --- | --- | --- |
| `LegacyWaterLine` | `WaterLine / Transmission Main` | `network_role = 'Transmission' AND lifecycle_status = 'Active'` | Select active transmission mains from a shared legacy line dataset. |
| `LegacyWaterLine` | `WaterLine / Distribution Main` | `network_role = 'Distribution' AND lifecycle_status = 'Active'` | Select active distribution mains for a separate target classification. |
| `LegacySewerLine` | `SewerLine / Gravity Main` | `flow_regime = 'Gravity' AND lifecycle_status <> 'Abandoned'` | Select in-scope gravity sewer mains while excluding abandoned assets. |

These expressions are illustrative. Field names, date syntax, coded values, quoting rules, and supported SQL operators depend on the source datastore.

Definition Query and filter QA should review:

- Whether every referenced field exists in the source schema and has a compatible data type.
- Whether the filter purpose and expected selection are documented.
- Whether a filter unexpectedly selects zero records.
- Whether filters overlap and could select or load the same source record more than once.
- Whether intentional gaps between filters are documented.
- Whether selected source counts reconcile with staged or loaded target counts.

## Civil Engineering Context for Asset Classification

Asset group and asset type mapping should consider the engineering meaning of an asset, not only similarities between source and target names. Civil engineering information can help document why a source asset belongs in a target classification and identify cases that require review.

Useful context can include:

| Engineering context | How it supports classification review |
| --- | --- |
| Facility function and network role | Distinguishes transmission, distribution, collection, conveyance, storage, control, and service functions. |
| Hydraulic operating mode | Separates pressurized, gravity, and open-channel assets. |
| Geometry and structure type | Helps distinguish lines, devices, junctions, structures, channels, culverts, and boundaries. |
| Material, lining, and coating | Refines asset types when the target schema classifies construction or rehabilitation characteristics. |
| Dimensions and capacity | Uses diameter, width, height, wall thickness, or design capacity to support the intended asset class. |
| Design and operating attributes | Uses pressure class, slope, invert elevation, flow direction, and terminal behavior to explain network function. |
| Installation and lifecycle context | Uses installation method, installation date, rehabilitation history, and lifecycle status to identify the appropriate current classification. |

Conceptual examples include:

- **Water:** Network role, pressure class, nominal diameter, and material can help distinguish a transmission main from a distribution main. A material match alone is not sufficient if the source record's function is unclear.
- **Wastewater:** Gravity flow, pipe slope, upstream and downstream inverts, and flow direction can support a gravity-main classification, while pressurized operation or a pump-discharge role can support a force-main classification.
- **Stormwater:** Conveyance form, cross-section dimensions, material, inlet and outlet context, and flow direction can help distinguish a closed pipe, culvert, open channel, or drainage structure.

Engineering context supports and documents the mapping decision. It does not replace the target schema, coded-value domains, connectivity and terminal rules, Utility Network design requirements, or review by qualified GIS and engineering staff.

## Main Toolkit Input and Output

### Input

| Input | Required | Description |
| --- | --- | --- |
| Source schema inventory | Yes | Source layers, tables, fields, data types, domains, geometry types, and record counts. |
| Target Utility Network schema metadata | Yes | Target feature classes, fields, required fields, domains, subtypes, asset groups, asset types, tiers, terminals, and rule expectations. |
| Source-to-target mapping table | Yes | CSV, Excel, YAML, JSON, or other structured mapping between source schema and target schema, including any filter assigned to each mapping pair. |
| Per-mapping Definition Queries or filters | Recommended | SQL-style expressions, their mapping purpose, and expected record scope for source-to-target selection. |
| Civil engineering context inventory | Recommended | Available network role, operating mode, geometry, material, dimensions, capacity, pressure, slope, invert, flow direction, installation, and lifecycle attributes used to support asset classification. |
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
| Definition Query and filter review report | Mapping pairs, referenced fields, empty selections, overlapping selections, and selected-versus-loaded record-count findings. |
| Asset classification rationale report | Engineering attributes used to support the selected asset group/type and unresolved classification questions requiring review. |
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
    require_filter_documentation: true
    flag_filter_field_mismatch: true
    flag_overlapping_filters: true
    warn_on_empty_selection: true
    compare_selected_to_loaded_counts: true
  domains:
    validate_coded_values: true
    validate_asset_groups: true
    validate_asset_types: true
    allow_unmapped_values: false
    require_asset_classification_rationale: true
    include_engineering_context_review: true
  data_reference:
    require_source_dataset: true
    require_target_dataset: true
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
- A Definition Query and filter review report.
- A required-field completeness report.
- A domain and asset-type compatibility report.
- An asset classification rationale report documenting relevant engineering context.
- A Data Reference workbook/configuration validation report.
- An attribute-rule readiness report.
- A network-rule coverage report.
- A dirty-area classification report, when dirty-area exports are provided.
- A final pass/warning/fail QA summary.

Expected practical benefits include:

- Earlier detection of schema and mapping problems.
- More auditable routing of source records through per-mapping filters.
- More consistent Utility Network loading configuration.
- More explainable asset group/type decisions based on available engineering context.
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
- Per-mapping Definition Query and filter review.
- Required field checker.
- Basic Markdown/HTML report.

### Version 0.2.0

- Domain validation.
- Asset group/type validation.
- Civil engineering context review for asset classification.
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

Keep credentials, tokens, secured URLs, connection strings, authentication profiles, sensitive infrastructure data, and restricted schema or mapping workbooks out of source control.

Recommended practices:

- Use synthetic or public sample data.
- Replace sensitive asset identifiers with generic placeholders.
- Avoid screenshots from secured systems.
- Remove URLs, connection strings, usernames, tokens, and internal file paths.
- Keep local connection files and restricted Data Reference workbooks or schema exports out of Git.
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
