# Synthetic Wastewater Migration Example

This example partitions a legacy sewer line inventory into gravity mains, force mains, and service laterals using one source-side Definition Query per mapping.

The gravity rule reviews slope and upstream/downstream invert context. The force-main rule reviews pressurized pump-discharge operation and pressure class. A pump terminal and two declared connectivity rules demonstrate terminal and rule-reference QA.

The service-lateral mapping intentionally has no matching engineering rule, so the expected result is `warning` with one `ASSET_RULE_NO_MATCH`. This is a review gap, not an automatic rejection or reclassification.

```bash
un-schema-qa validate examples/wastewater/project.yml
```

All data and identifiers are synthetic.

