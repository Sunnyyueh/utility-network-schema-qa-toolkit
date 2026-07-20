# Synthetic Water Migration Example

This runnable example splits one legacy water-line source into transmission and distribution mappings. Each mapping owns a source-side Definition Query, documented purpose, expected/selected/loaded counts, target classification, and civil-engineering rationale.

Both mapping partitions also demonstrate metadata-level field QA for three Utility Network concerns:

- `lifecycle_status` uses source and target coded-value domains with explicit `target_code` crosswalks.
- `owner` maps text fields with sufficient target length and a documented normalization expression.
- `elevation` declares US survey feet to metres, a conversion expression, and NAVD88 on both sides.

Run it from the repository root:

```bash
un-schema-qa validate examples/water/project.yml
```

The expected result is `warning`: two informational `ASSET_RULE_MATCH` findings document the explainable rule matches, and one synthetic `DIRTY_AREA_GROUP` warning demonstrates remediation grouping. All names, counts, identifiers, and infrastructure records are synthetic.

The engineering and field-semantic rules support review; they do not read feature records, execute expressions, alter mappings, or replace target domains, Utility Network rules, or engineering approval.
