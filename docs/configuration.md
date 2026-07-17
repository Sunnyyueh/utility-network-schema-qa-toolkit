# Project Configuration

The project manifest is strict YAML. Unknown keys and invalid enum values fail before validation begins. Relative input and output paths resolve from the manifest directory.

```yaml
project:
  name: water-migration
  profile: water
inputs:
  source_schema: data/source_schema.csv
  target_schema: data/target_schema.xlsx
  mappings: data/mappings.csv
  source_domains: data/source_domains.csv
  target_domains: data/target_domains.csv
  asset_types: data/asset_types.csv
  data_reference: data/data_reference.csv
  attribute_rules: data/attribute_rules.csv
  network_rules: data/network_rules.csv
  terminals: data/terminals.csv
  dirty_areas: data/dirty_areas.csv
  engineering_rules: rules/engineering.yml
validation:
  enabled: [schema, mapping, filters, domains, asset_classification]
  fail_on: error
  severity_overrides:
    FILTER_EXPECTED_COUNT_MISSING: info
outputs:
  directory: reports
  formats: [json, csv, markdown, html]
```

## Project

`project.name` is required. `project.profile` is optional and accepts `water`, `wastewater`, or `stormwater`.

## Inputs

`source_schema`, `target_schema`, and `mappings` are required. All other inputs are optional. Optional validators are skipped when their primary inventory is absent. Domain and asset checks still run when schema or mapping references require those inventories.

## Validation

`enabled` accepts stable names listed in [Validation Rules](validation-rules.md). `severity_overrides` maps an exact finding code to `info`, `warning`, or `error`. Overrides do not hide findings. `fail_on` records the project policy; CLI exit behavior is described in [CLI](cli.md).

## Outputs

`directory` is created if needed. Existing fixed report files in that directory are atomically replaced. Formats are `json`, `csv`, `markdown`, and `html`; duplicates and unknown formats are rejected.

Use only paths and exports appropriate for the intended reviewers. Keep credentials, tokens, secured service URLs, authentication profiles, connection strings, and sensitive infrastructure records out of manifests and generated reports.

