# Wastewater Tutorial

The synthetic wastewater project partitions one legacy line dataset into gravity mains, force mains, and service laterals.

## Run

```bash
un-schema-qa validate examples/wastewater/project.yml --output wastewater-reports
```

Expected status is `warning`: gravity and force-main rules match, while the service lateral intentionally produces `ASSET_RULE_NO_MATCH`.

## Gravity review

The gravity mapping supplies flow regime, slope, and upstream/downstream inverts. The YAML rule requires positive slope and decreasing invert context. Edit slope to a negative value to make the rule gap visible.

## Force-main and terminal review

The force-main mapping supplies pressurized pump-discharge context and pressure class. The network inventory declares a lift-station pump `Discharge` terminal connected to the force main. Rename the terminal in one inventory to observe terminal-reference QA.

The service rule gap is deliberate: it shows that engineering rules support review without forcing a target or changing the mapping.

