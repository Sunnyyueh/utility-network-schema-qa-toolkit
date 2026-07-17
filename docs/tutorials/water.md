# Water Tutorial

The synthetic water project demonstrates two mappings from `LegacyWaterLine` to `WaterLine`: transmission and distribution mains.

## Run

```bash
un-schema-qa validate examples/water/project.yml --output water-reports
```

Expected status is `warning`. Two `ASSET_RULE_MATCH` findings explain the engineering classifications. One `DIRTY_AREA_GROUP` warning demonstrates remediation grouping.

## Review the filters

Open `examples/water/data/mappings.csv`. Each mapping has a mutually exclusive `network_role` filter, purpose, expected count, selected count, loaded count, classification, and rationale. Change a selected count and rerun to see count reconciliation. Change one filter to include both roles to see overlap detection.

## Review classification

Open `examples/water/rules/engineering_rules.yml`. Transmission requires transmission role, active lifecycle, and diameter at or above 600. Distribution requires distribution role, active lifecycle, and diameter below 600. Change a mapped asset type to observe `ASSET_RULE_DISAGREEMENT`.

Review JSON for automation, HTML for stakeholder review, and CSV for downstream analysis. Restore the synthetic file after experimentation.

