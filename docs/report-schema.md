# Report Formats and Schema

Every report contains project name, toolkit version, input fingerprint, status, counts, validators, and findings. Filenames are fixed: `validation-report.json`, `validation-report.csv`, `validation-report.md`, and `validation-report.html`.

## `json`

JSON is the canonical machine-readable representation. Its contract is [validation-report-v1.schema.json](../schemas/validation-report-v1.schema.json). The `schema_version` value is `1.0`; incompatible future changes require another schema file/version.

Top-level properties are:

- `schema_version`
- `toolkit_version`
- `project_name`
- `input_fingerprint`
- `validators`
- `findings`
- `summary`

Each finding includes code, severity, validator, message, recommendation, affected dataset/field/mapping, optional source location, and JSON details.

## `csv`

CSV contains one row per finding and repeats run metadata on each row. Structured details are compact JSON. An empty result still contains the header row. Standard CSV quoting preserves commas, quotes, and newlines.

## `markdown`

Markdown provides a summary table and validator-grouped finding tables suitable for GitHub review. Table separators and line breaks in user values are escaped.

## `html`

HTML is self-contained, responsive, accessible, and autoescaped. It contains embedded CSS but no script, external URL, font, image, or network request.

Writers create the selected directory, use same-directory temporary files, flush them, and atomically replace only the fixed destination names. Unknown/path-like formats and file-valued output directories are rejected.

