# Stormwater Tutorial

The synthetic stormwater project maps linear assets to pipes, culverts, and open channels, and point assets to grate inlets.

## Run

```bash
un-schema-qa validate examples/stormwater/project.yml --output stormwater-reports
```

Expected status is `fail` because the dirty-area export contains one error-level connectivity group. Four informational `ASSET_RULE_MATCH` findings explain the mapped asset forms.

## Review asset forms

The mapping inventory uses `structure_type`, geometry, width, and height. The source-side filters partition `Pipe`, `Culvert`, and `Open Channel` rows. A separate point source selects `Inlet` structures.

## Review dirty areas

Two code-100 records aggregate into one warning-level geometry group. One code-200 record produces an error-level connectivity group. Change its severity to `warning` and rerun to see aggregate status become warning.

The network-rule inventory connects pipes to inlets and culverts to open channels, giving every mapped classification declared coverage without attempting a live network trace.

