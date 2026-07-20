# Utility Network Schema QA Toolkit

`utility-network-schema-qa-toolkit` V1.0 is an open-source, MIT-licensed Python toolkit for validating exported Utility Network schemas, source-to-target mappings, per-mapping Definition Queries, domains, asset classifications, declared rules, Data Reference inventories, dirty-area exports, and migration QA reports.

It works with CSV, TSV, JSON, YAML, XLSX, and XLSM artifacts without ArcPy or a proprietary GIS runtime. It does not connect to or modify a live Utility Network.

## What V1.0 provides

- Strict project manifests and immutable canonical data models.
- Header aliases for common schema, mapping, and Data Reference workbook exports.
- Safe, non-executing analysis of a documented SQL-style filter subset.
- Source/target dataset, field, geometry, required-field, type, and transformation QA.
- Metadata-level `lifecycle_status`, `owner`, and `elevation` field mapping QA.
- Domain, coded-value, explicit crosswalk, asset group, and asset type QA.
- Explainable YAML civil-engineering classification rules with deterministic priority.
- Data Reference, attribute-rule dependency, network-rule, terminal, and dirty-area checks.
- Stable Finding codes, exact-code severity overrides, deterministic sorting, and SHA-256 fingerprints.
- JSON, CSV, Markdown, and self-contained accessible HTML reports.
- A Python API and the `un-schema-qa` command-line interface.
- Complete synthetic water, wastewater, and stormwater projects.

The toolkit reviews exported metadata and declared relationships. It does not execute SQL, Arcade, or Python from inputs; perform a data load; build topology; trace a network; or replace engineering review.

## Installation

Python 3.10 or newer is required. Install the latest stable release from [PyPI](https://pypi.org/project/utility-network-schema-qa-toolkit/):

```bash
python -m pip install utility-network-schema-qa-toolkit
```

Pin the V1.0 release when reproducible environments require an exact version:

```bash
python -m pip install "utility-network-schema-qa-toolkit==1.0.0"
```

Upgrade an existing installation:

```bash
python -m pip install --upgrade utility-network-schema-qa-toolkit
```

To install the current repository checkout instead:

```bash
python -m pip install .
```

Verify the installation:

```bash
un-schema-qa version
un-schema-qa list-checks
```

The version command prints `un-schema-qa 1.0.0` for this release.

## Quick start

Create a starter project:

```bash
un-schema-qa init my-water-qa --profile water
un-schema-qa validate my-water-qa/project.yml
```

Run a complete repository example:

```bash
un-schema-qa validate examples/water/project.yml
un-schema-qa validate examples/wastewater/project.yml
un-schema-qa validate examples/stormwater/project.yml
```

Reports are written to the manifest's output directory. Override the destination or formats when needed:

```bash
un-schema-qa validate examples/water/project.yml \
  --output review-reports \
  --format json \
  --format html
```

Exit codes are `0` for pass (and warnings by default), `1` for warnings with `--fail-on-warning`, `2` for validation failure, and `3` for configuration/input/runtime errors.

## Project manifest

Only source schema, target schema, and mappings are required. Other inventories activate additional checks. These files should contain real exported metadata from the source system and intended target Utility Network: dataset and field definitions, domains, mapping decisions, rules, and recorded counts. They do not need feature records, geometry, credentials, or a live Utility Network connection.

This separation makes reviews repeatable and allows schema QA before loading. It does not make placeholder metadata equivalent to a production review: results are only as complete as the exported schemas, domains, mappings, and counts supplied to the manifest.

```yaml
project:
  name: water-migration
  profile: water
inputs:
  source_schema: data/source_schema.csv
  target_schema: data/target_schema.csv
  mappings: data/mappings.csv
  source_domains: data/source_domains.csv
  target_domains: data/target_domains.csv
  asset_types: data/asset_types.csv
  data_reference: data/data_reference.csv
  attribute_rules: data/attribute_rules.csv
  network_rules: data/network_rules.csv
  terminals: data/terminals.csv
  dirty_areas: data/dirty_areas.csv
  engineering_rules: rules/engineering_rules.yml
validation:
  enabled: [schema, mapping, field_semantics, filters, domains, asset_classification]
  fail_on: error
  severity_overrides:
    FILTER_EXPECTED_COUNT_MISSING: info
outputs:
  directory: reports
  formats: [json, csv, markdown, html]
```

Relative paths resolve from `project.yml`. Unknown manifest keys, checks, profiles, severities, and formats fail early.

## Field-level Utility Network mapping QA

Add `semantic_role` and supporting metadata to individual source-to-target field rows. Roles are explicit; the toolkit does not infer them from field names.

Enable `field_semantics` in the manifest. Elevation rows also declare `source_vertical_datum` and `target_vertical_datum`, along with source/target units.

```csv
mapping_id,source_dataset,target_dataset,source_field,target_field,expression,semantic_role,source_unit,target_unit,source_vertical_datum,target_vertical_datum,field_rationale
water-main,LegacyWaterLine,WaterLine,status,lifecycle_status,,lifecycle_status,,,,,Crosswalk legacy values to the target lifecycle domain
water-main,LegacyWaterLine,WaterLine,owner_name,owner,UPPER(owner_name),owner,,,,,Normalize owner names for stewardship review
water-main,LegacyWaterLine,WaterLine,elevation_ft,elevation,elevation_ft * 0.3048006096,elevation,us_survey_ft,m,NAVD88,NAVD88,Convert surveyed elevations to target metres
```

| `semantic_role` | Metadata QA performed |
| --- | --- |
| `lifecycle_status` | Requires domains on both fields so source codes and explicit `target_code` crosswalks can be reviewed. |
| `owner` | Requires text fields, checks known source/target lengths for truncation risk, and flags one-sided domain use. |
| `elevation` | Requires numeric fields, supported source/target units, vertical datum metadata, and an expression when units or datums differ. |

Run the complete manifest or isolate this check:

```bash
un-schema-qa validate project.yml
un-schema-qa validate project.yml --check field_semantics
```

The validator compares exported schema and mapping metadata only. It does not inspect lifecycle, owner, or elevation values in feature records; execute expressions; verify conversion constants or coordinate operations; or automatically score and select an asset group/type. Findings identify metadata gaps and review risks, while target domains, Utility Network rules, and qualified engineering review remain authoritative.

## Per-mapping Definition Queries and filters

Every source-to-target mapping may carry its own source-side SQL-style filter. This lets one source dataset route different record populations to different target datasets, asset groups, or asset types.

| Source | Target classification | Definition Query | Purpose |
| --- | --- | --- | --- |
| `LegacyWaterLine` | `WaterLine / Transmission Main` | `network_role = 'Transmission' AND lifecycle_status = 'Active'` | Select active transmission mains. |
| `LegacyWaterLine` | `WaterLine / Distribution Main` | `network_role = 'Distribution' AND lifecycle_status = 'Active'` | Select active distribution mains. |
| `LegacySewerLine` | `WastewaterLine / Gravity Main` | `flow_regime = 'Gravity' AND lifecycle_status <> 'Abandoned'` | Select in-scope gravity mains. |

Each mapping can also record `purpose`, `expected_count`, `selected_count`, and `loaded_count`. The filter validator checks:

- supported syntax and balanced expressions;
- fields referenced by the source-side filter;
- missing purpose or expected scope;
- recorded empty selections;
- expected-versus-selected and selected-versus-loaded count differences;
- missing filters when one source is split into multiple mappings; and
- possible overlap for simple equality/`IN` partitions.

Overlap analysis is deliberately conservative. It can prove simple partitions disjoint or flag possible overlap; complex expressions return unknown rather than an unsafe guarantee. Datastore-specific SQL semantics remain the responsibility of the project team. The toolkit does not define a target-side Definition Query feature.

## Civil-engineering-informed asset classification

Mapping by similar names alone is often insufficient. V1.0 can evaluate explicit YAML rules against engineering context and report the rule ID, target classification, explanation, missing attributes, conflicts, and disagreement with the selected mapping.

Useful context includes:

| Context | Review use |
| --- | --- |
| Facility function and network role | Transmission, distribution, collection, service, storage, or control. |
| Hydraulic operation | Pressurized, gravity, or open-channel behavior. |
| Geometry and structure type | Pipe, device, culvert, channel, inlet, junction, or other structure form. |
| Material, lining, and coating | Construction and rehabilitation distinctions. |
| Diameter, width, height, and capacity | Scale, section, and design function. |
| Pressure class, slope, invert, and flow direction | Operating and conveyance behavior. |
| Installation and lifecycle context | Installation method/date and current asset state. |

Conceptual examples:

- Water transmission versus distribution mains can use network role, pressure class, nominal diameter, and lifecycle status.
- Wastewater gravity mains can use gravity regime, positive slope, and upstream/downstream inverts; force mains can use pressurized pump-discharge operation.
- Stormwater classification can distinguish closed pipes, culverts, open channels, and point structures using geometry, structure form, and cross-section dimensions.

Example rule:

```yaml
rules:
  - rule_id: wastewater-gravity-main
    priority: 10
    conditions:
      - field: flow_regime
        operator: equals
        value: gravity
      - field: slope
        operator: greater_than
        value: 0
    target_asset_group: Main
    target_asset_type: Gravity Main
    explanation: Gravity operation with positive slope supports gravity conveyance.
```

Allowed operators are `equals`, `not_equals`, `in`, `not_in`, `greater_than`, `greater_or_equal`, `less_than`, `less_or_equal`, `exists`, and `contains`. Rules support `all` or `any` condition mode and never change a mapping. Engineering attributes support and document a decision; they do not replace target domains, Utility Network rules, design standards, or review by qualified GIS and engineering staff.

## Python API

```python
from pathlib import Path
from un_schema_qa import load_project, validate_project, write_reports

project = load_project(Path("project.yml"))
result = validate_project(project)
paths = write_reports(result, formats=("json", "html"))
```

`ValidationResult` includes project name, toolkit/schema versions, fingerprint, validators actually run, sorted findings, counts, and aggregate status.

## Examples

- [Water example](examples/water/README.md): transmission/distribution filters, engineering rule matches, Data Reference partitions, and dirty-area grouping.
- [Wastewater example](examples/wastewater/README.md): gravity/force-main rules, slope/inverts, pump terminal, and a deliberate rule gap.
- [Stormwater example](examples/stormwater/README.md): pipes, culverts, open channels, structures, and two dirty-area groups.

All example names, counts, identifiers, and infrastructure records are synthetic.

## Documentation

- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Input formats and aliases](docs/input-formats.md)
- [Validation rules](docs/validation-rules.md)
- [Finding code catalog](docs/finding-codes.md)
- [Python API](docs/python-api.md)
- [CLI](docs/cli.md)
- [Report schema](docs/report-schema.md)
- [Water tutorial](docs/tutorials/water.md)
- [Wastewater tutorial](docs/tutorials/wastewater.md)
- [Stormwater tutorial](docs/tutorials/stormwater.md)

## Development and governance

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

Quality commands:

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

## Security

Do not commit credentials, tokens, secured service URLs, connection strings, authentication profiles, restricted schema workbooks, or sensitive infrastructure data. Treat terminal logs and generated reports as review artifacts: inspect them before sharing and store them according to their data classification.

The toolkit performs no network requests and does not evaluate input SQL, Arcade, Python, or template expressions.

## License

Released under the [MIT License](LICENSE).
