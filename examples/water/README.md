# Synthetic Water Migration Example

This runnable example splits one legacy water-line source into transmission and distribution mappings. Each mapping owns a source-side Definition Query, documented purpose, expected/selected/loaded counts, target classification, and civil-engineering rationale.

Run it from the repository root:

```bash
un-schema-qa validate examples/water/project.yml
```

The expected result is `warning`: two informational `ASSET_RULE_MATCH` findings document the explainable rule matches, and one synthetic `DIRTY_AREA_GROUP` warning demonstrates remediation grouping. All names, counts, identifiers, and infrastructure records are synthetic.

The engineering rules support review; they do not alter mappings or replace target domains, Utility Network rules, or engineering approval.

