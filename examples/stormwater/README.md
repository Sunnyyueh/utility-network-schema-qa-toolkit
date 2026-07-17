# Synthetic Stormwater Migration Example

This example separates legacy linear conveyance into pipes, culverts, and open channels, while mapping point structures to grate inlets. Every mapping has its own source-side Definition Query and a civil-engineering rationale based on geometry, structure form, and section dimensions.

Two network rules cover all four mapped classifications. The dirty-area export intentionally creates two groups: a warning-level geometry review and an error-level connectivity review. The expected overall result is therefore `fail`, demonstrating how a release gate can identify unresolved synthetic issues.

```bash
un-schema-qa validate examples/stormwater/project.yml
```

All data and identifiers are synthetic.

