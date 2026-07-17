# Architecture

Utility Network Schema QA Toolkit is a license-free Python validation pipeline. It reads exported metadata and migration artifacts; it does not open a geodatabase, execute ArcPy, trace a Utility Network, or load records.

## Pipeline

1. `load_config` parses and resolves `project.yml`.
2. Format readers convert CSV, JSON, YAML, and XLSX sheets into neutral rows.
3. Loaders normalize aliases and build immutable Pydantic models.
4. The validator registry runs enabled checks in a stable order.
5. Findings receive stable codes, severities, source locations, and recommendations.
6. The engine applies exact-code severity overrides, deduplicates, sorts, and fingerprints results.
7. Reporters render JSON, CSV, Markdown, and self-contained HTML.

## Module boundaries

- `config.py` owns strict manifest validation.
- `readers/` owns file decoding and workbook sheet selection.
- `models/` defines the canonical project and result contracts.
- `filters.py` tokenizes a non-executing SQL-style subset.
- `rules.py` evaluates explicit civil-engineering conditions.
- `validators/` contains independent, read-only QA checks.
- `engine.py` owns ordering, optional-input skipping, overrides, and failures.
- `api.py` is the stable Python entry point.
- `reporters/` owns serialization and atomic report replacement.
- `cli.py` is a thin command wrapper around those public capabilities.

## Safety boundaries

Input SQL, Arcade, Python, and other expressions are stored or tokenized but never evaluated. Engineering rules can recommend and explain classifications but never mutate a mapping. HTML uses unconditional autoescaping and contains no external script or network resource. Report writers use fixed filenames inside the selected output directory.

## Extension model

New readers should return `TabularRows`. New checks implement the `Validator` protocol and can be registered in a `ValidatorRegistry`. New canonical fields require model, alias, loader, documentation, and test updates together. Report schema changes require a new schema version rather than silently changing the V1 contract.

