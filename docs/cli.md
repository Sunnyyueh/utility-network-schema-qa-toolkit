# Command-Line Interface

Install the package and run `un-schema-qa --help`.

## `validate`

```text
un-schema-qa validate PROJECT.yml [--output DIR] [--format FORMAT] [--check NAME] [--fail-on-warning] [--debug]
```

`--format` and `--check` may be repeated. Without overrides, output directory/formats and enabled checks come from the manifest. Exit codes are `0` for pass (and warnings by default), `1` for warning with `--fail-on-warning`, `2` for validation failure, and `3` for configuration/input/runtime errors.

## `inspect-workbook`

```text
un-schema-qa inspect-workbook mapping.xlsx
```

Lists every sheet, non-empty data-row count, and detected header row. It never modifies the workbook.

## `init`

```text
un-schema-qa init starter --profile wastewater
```

Creates a minimal synthetic starter for `water`, `wastewater`, or `stormwater`. Existing starter files are protected unless `--force` is explicit; unrelated files are never removed.

## `list-checks`

Prints stable validator names and short descriptions for manifest or `--check` use.

## `version`

Prints the installed distribution version.

Errors are concise by default. `--debug` adds a traceback for diagnosis. Avoid including credentials, tokens, secured URLs, connection strings, authentication profiles, or sensitive infrastructure values in terminal logs and generated reports.

