# Utility Network Schema QA Toolkit V1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and release a genuinely installable, license-free V1.0 Python toolkit for validating exported Utility Network schemas, mappings, filters, domains, asset classifications, rules, dirty areas, and QA reports.

**Architecture:** Format-specific readers normalize files into canonical Pydantic models. Independent validators return stable findings through a shared engine, and reporters serialize one validation result into JSON, CSV, Markdown, and HTML. The CLI and Python API share the same configuration, engine, and error model.

**Tech Stack:** Python 3.10+, Hatchling, Pydantic 2, Typer, PyYAML, openpyxl, Jinja2, pytest, pytest-cov, Ruff, mypy.

## Global Constraints

- No ArcPy, ArcGIS license, database, feature-service, or proprietary runtime dependency.
- No network requests, arbitrary expression execution, hidden scoring, or automatic schema mutation.
- Only source schema, target schema, and mapping inputs are required; optional validators report skipped inputs.
- Finding codes, report ordering, filenames, CLI exit codes, and JSON schema are deterministic.
- Public API: `load_project`, `validate_project`, and `write_reports`.
- CLI: `validate`, `inspect-workbook`, `init`, `list-checks`, and `version`.
- Every implementation task follows red-green-refactor and ends in a meaningful commit.
- Coverage threshold is 90 percent for `src/un_schema_qa`.

---

### Task 1: Repository and Package Foundation

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `src/un_schema_qa/__init__.py`
- Create: `src/un_schema_qa/version.py`
- Create: `src/un_schema_qa/exceptions.py`
- Create: `tests/test_package.py`

**Interfaces:**
- Produces `un_schema_qa.__version__: str`.
- Produces `ConfigurationError`, `InputFormatError`, `WorkbookDetectionError`, and `ValidationExecutionError`.

- [ ] Write `tests/test_package.py` asserting the package exports a semantic version and typed exceptions inherit from `ToolkitError`.
- [ ] Run `python -m pytest tests/test_package.py -v`; expect import failure.
- [ ] Add Hatchling build metadata, runtime/dev dependencies, Ruff/mypy/pytest configuration, `un-schema-qa` console entry point, MIT license, ignore rules, version `1.0.0`, and exception hierarchy.
- [ ] Run `python -m pytest tests/test_package.py -v`; expect pass.
- [ ] Run `python -m pip install -e '.[dev]'` and `python -m build`; expect wheel and sdist.
- [ ] Commit with `chore: establish package foundation`.

### Task 2: Core Enums, Source Locations, and Findings

**Files:**
- Create: `src/un_schema_qa/models/common.py`
- Create: `src/un_schema_qa/models/findings.py`
- Create: `src/un_schema_qa/models/__init__.py`
- Create: `tests/models/test_findings.py`

**Interfaces:**
- Produces `Severity(INFO, WARNING, ERROR)`, `RunStatus(PASS, WARNING, FAIL)`, and `SourceLocation(path, sheet, row, column)`.
- Produces `Finding(code, severity, validator, message, recommendation, dataset, field, mapping_id, location, details)`.
- Produces `ValidationSummary` and `ValidationResult` with `from_findings()`.

- [ ] Write tests for severity ordering, finding identity keys, deterministic sorting, summary counts, and pass/warning/fail calculation.
- [ ] Run the focused tests; expect missing-model failure.
- [ ] Implement strict Pydantic models, enums, finding deduplication keys, stable sort keys, and summary construction.
- [ ] Run the focused tests; expect pass.
- [ ] Commit with `feat: add findings and run result models`.

### Task 3: Schema, Mapping, Domain, and Rule Models

**Files:**
- Create: `src/un_schema_qa/models/schema.py`
- Create: `src/un_schema_qa/models/mapping.py`
- Create: `src/un_schema_qa/models/rules.py`
- Create: `src/un_schema_qa/models/project.py`
- Create: `tests/models/test_domain_models.py`

**Interfaces:**
- Produces the canonical models named in the design spec.
- `ProjectData` groups source/target datasets and all optional inventories.
- Collections expose case-insensitive `dataset(name)`, `field(name)`, `domain(name)`, and `asset_type(group, type)` lookups.

- [ ] Write tests for type normalization, case-insensitive lookups, duplicate-key rejection, engineering-context extras, and project defaults.
- [ ] Run focused tests; expect missing-model failure.
- [ ] Implement models with frozen values where practical, explicit aliases, and lookup helpers.
- [ ] Run focused tests; expect pass.
- [ ] Commit with `feat: define canonical project models`.

### Task 4: Column Aliases and Primitive Normalization

**Files:**
- Create: `src/un_schema_qa/normalization.py`
- Create: `tests/test_normalization.py`

**Interfaces:**
- `normalize_header(value: str) -> str`.
- `resolve_columns(headers: Sequence[str], logical_schema: Mapping[str, set[str]]) -> dict[str, str]`.
- `parse_bool`, `parse_int`, `parse_float`, `parse_list`, `normalize_data_type`, and `normalize_geometry_type`.

- [ ] Write table-driven tests for common Esri headers, booleans, nulls, data-type aliases, comma-separated lists, and ambiguous column aliases.
- [ ] Run tests; expect missing implementation.
- [ ] Implement pure deterministic normalization with `InputFormatError` for ambiguous required columns.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: normalize workbook and schema values`.

### Task 5: Project Configuration Loader

**Files:**
- Create: `src/un_schema_qa/config.py`
- Create: `tests/test_config.py`
- Create: `tests/fixtures/config/minimal.yml`
- Create: `tests/fixtures/config/complete.yml`

**Interfaces:**
- `ProjectConfig`, `InputConfig`, `ValidationConfig`, and `OutputConfig` models.
- `load_config(path: Path) -> ProjectConfig` resolves all paths relative to the manifest.

- [ ] Write tests for minimal/complete YAML, unknown keys, missing required paths, relative resolution, enabled checks, fail-on severity, and overrides.
- [ ] Run tests; expect failure.
- [ ] Implement strict YAML loading and path resolution without reading referenced data files.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: load strict project configuration`.

### Task 6: CSV, JSON, and YAML Readers

**Files:**
- Create: `src/un_schema_qa/readers/base.py`
- Create: `src/un_schema_qa/readers/delimited.py`
- Create: `src/un_schema_qa/readers/structured.py`
- Create: `src/un_schema_qa/readers/registry.py`
- Create: `src/un_schema_qa/readers/__init__.py`
- Create: `tests/readers/test_structured_readers.py`
- Create: `tests/fixtures/readers/*`

**Interfaces:**
- `TabularRows(headers, rows, locations)` is the reader-neutral table representation.
- `read_rows(path: Path, *, sheet: str | None = None) -> TabularRows` dispatches by suffix.
- Structured files accept row arrays and identifier-keyed objects.

- [ ] Write reader contract tests for CSV quoting, UTF-8 BOM, JSON arrays/objects, YAML arrays/objects, empty files, malformed input, and source locations.
- [ ] Run tests; expect failure.
- [ ] Implement readers and registry with typed errors.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: read structured schema inputs`.

### Task 7: XLSX Reading and Workbook Inspection

**Files:**
- Create: `src/un_schema_qa/readers/excel.py`
- Create: `src/un_schema_qa/workbooks.py`
- Create: `tests/readers/test_excel_reader.py`
- Create: `tests/test_workbooks.py`

**Interfaces:**
- `read_xlsx_rows(path, sheet=None) -> TabularRows`.
- `inspect_workbook(path: Path) -> WorkbookInspection`.
- `detect_sheet(workbook, logical_schema) -> str` returns one unambiguous sheet or raises `WorkbookDetectionError` with candidates.

- [ ] Generate fixture workbooks in tests and cover explicit sheet selection, header detection, blank rows, formulas as cached values, aliases, ambiguity, and missing sheets.
- [ ] Run tests; expect failure.
- [ ] Implement read-only openpyxl loading, sheet scoring, inspection output, and location capture.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: inspect and read Excel workbooks`.

### Task 8: Canonical Project Data Loader

**Files:**
- Create: `src/un_schema_qa/loaders.py`
- Create: `src/un_schema_qa/row_schemas.py`
- Create: `tests/test_loaders.py`

**Interfaces:**
- `load_project_data(config: ProjectConfig) -> ProjectData`.
- Dedicated row converters build each canonical model and preserve unknown columns under `extra`.

- [ ] Write integration tests loading minimal and complete mixed-format projects and verifying source locations and optional inventories.
- [ ] Run tests; expect failure.
- [ ] Implement logical row schemas, alias resolution, grouping, conversions, and optional-input handling.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: load canonical project data`.

### Task 9: Safe Definition Query Analysis

**Files:**
- Create: `src/un_schema_qa/filters.py`
- Create: `tests/test_filters.py`

**Interfaces:**
- `analyze_filter(expression: str) -> FilterAnalysis` with identifiers, predicates, tokens, errors, and a simple partition signature.
- `possible_overlap(left: FilterAnalysis, right: FilterAnalysis) -> bool | None` returns unknown rather than making unsafe claims.

- [ ] Write tests for comparisons, `IN`, `LIKE`, null checks, parentheses, boolean operators, quoted strings, dates, unbalanced syntax, unknown tokens, and equality partition overlap.
- [ ] Run tests; expect failure.
- [ ] Implement a non-executing tokenizer and recursive validation of the documented subset.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: analyze mapping definition queries safely`.

### Task 10: Explainable Engineering Rule Engine

**Files:**
- Create: `src/un_schema_qa/rules.py`
- Create: `tests/test_engineering_rules.py`
- Create: `tests/fixtures/rules/engineering.yml`

**Interfaces:**
- `load_engineering_rules(path: Path) -> tuple[EngineeringRule, ...]`.
- `evaluate_engineering_rules(context, rules) -> RuleEvaluation` returning ordered matches and explanations.

- [ ] Write tests for every allowed operator, priority ordering, missing attributes, no match, one match, conflicting matches, and invalid operator rejection.
- [ ] Run tests; expect failure.
- [ ] Implement explicit operator functions and deterministic evaluation; never mutate mappings.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: evaluate civil engineering classification rules`.

### Task 11: Validator Framework and Schema Validator

**Files:**
- Create: `src/un_schema_qa/validators/base.py`
- Create: `src/un_schema_qa/validators/schema.py`
- Create: `src/un_schema_qa/validators/__init__.py`
- Create: `tests/validators/test_schema_validator.py`

**Interfaces:**
- `ValidationContext(project, config)`.
- `Validator` protocol with `name`, `required_inputs`, and `validate(context) -> list[Finding]`.
- `SchemaValidator` emits the schema finding codes in the design.

- [ ] Write tests for duplicates, unsupported types, required metadata, nullability/default conflict, geometry mismatch, subtype/asset field references, and compatible schema.
- [ ] Run tests; expect failure.
- [ ] Implement framework helpers and schema checks with stable codes and recommendations.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: validate source and target schemas`.

### Task 12: Mapping and Filter Validators

**Files:**
- Create: `src/un_schema_qa/validators/mapping.py`
- Create: `src/un_schema_qa/validators/filters.py`
- Create: `tests/validators/test_mapping_validator.py`
- Create: `tests/validators/test_filter_validator.py`

**Interfaces:**
- `MappingValidator` validates datasets, fields, required targets, types, duplicates, expressions, and lookups.
- `FilterValidator` uses `analyze_filter` and emits field, syntax, documentation, count, and overlap findings.

- [ ] Write failing tests for every documented mapping/filter behavior, including one-source-to-multiple-target partitions.
- [ ] Run tests; expect failure.
- [ ] Implement both validators using shared compatibility and finding helpers.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: validate mappings and definition queries`.

### Task 13: Domain and Asset Classification Validators

**Files:**
- Create: `src/un_schema_qa/validators/domains.py`
- Create: `src/un_schema_qa/validators/assets.py`
- Create: `tests/validators/test_domain_validator.py`
- Create: `tests/validators/test_asset_validator.py`

**Interfaces:**
- `DomainValidator` checks definitions, crosswalks, defaults, and coded values.
- `AssetClassificationValidator` checks target inventories, rationale, and engineering rule results.

- [ ] Write tests for missing/duplicate domains, unmapped values, invalid defaults, unknown asset types, missing rationale, no/single/conflicting rule matches, and mapping disagreement.
- [ ] Run tests; expect failure.
- [ ] Implement validators and stable finding catalog entries.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: validate domains and asset classifications`.

### Task 14: Data Reference and Dependency Validators

**Files:**
- Create: `src/un_schema_qa/validators/data_reference.py`
- Create: `src/un_schema_qa/validators/attribute_rules.py`
- Create: `tests/validators/test_data_reference_validator.py`
- Create: `tests/validators/test_attribute_rule_validator.py`

**Interfaces:**
- Data Reference checks files relative to the project manifest and mapping consistency.
- Attribute-rule checks validate declared metadata without executing expressions.

- [ ] Write tests for required references, duplicates, missing files, inconsistent query/mapping IDs, disabled rows, dependencies, domain readiness, trigger values, and duplicate names.
- [ ] Run tests; expect failure.
- [ ] Implement the validators with skipped-input behavior handled by the engine.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: validate data references and attribute rules`.

### Task 15: Network Rule and Dirty Area Validators

**Files:**
- Create: `src/un_schema_qa/validators/network_rules.py`
- Create: `src/un_schema_qa/validators/dirty_areas.py`
- Create: `tests/validators/test_network_rule_validator.py`
- Create: `tests/validators/test_dirty_area_validator.py`

**Interfaces:**
- Network-rule validation references target asset and terminal inventories.
- Dirty-area validation groups issues and applies configured remediation categories.

- [ ] Write tests for unknown assets/terminals, duplicate and contradictory rules, mapped-classification coverage, missing dirty-area identifiers, known/unknown codes, grouping, and remediation.
- [ ] Run tests; expect failure.
- [ ] Implement both validators with deterministic findings.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: validate network rules and dirty areas`.

### Task 16: Validation Engine and Public Python API

**Files:**
- Create: `src/un_schema_qa/engine.py`
- Create: `src/un_schema_qa/api.py`
- Modify: `src/un_schema_qa/__init__.py`
- Create: `tests/test_engine.py`
- Create: `tests/test_api.py`

**Interfaces:**
- `build_default_registry() -> ValidatorRegistry`.
- `validate_project(project_or_path, *, checks=None) -> ValidationResult`.
- `load_project(path) -> ProjectData`.

- [ ] Write tests for validator order, enable/disable, missing optional inputs, severity overrides, deduplication, status, input fingerprint, validator exceptions, and top-level API.
- [ ] Run tests; expect failure.
- [ ] Implement registry, orchestration, metadata, and exported API.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: orchestrate validation through public API`.

### Task 17: Machine-Readable Reporters

**Files:**
- Create: `src/un_schema_qa/reporters/base.py`
- Create: `src/un_schema_qa/reporters/json_report.py`
- Create: `src/un_schema_qa/reporters/csv_report.py`
- Create: `src/un_schema_qa/reporters/__init__.py`
- Create: `schemas/validation-report-v1.schema.json`
- Create: `tests/reporters/test_machine_reports.py`

**Interfaces:**
- `write_reports(result, output_dir=None, formats=(...)) -> dict[str, Path]`.
- `render_json(result) -> str` and `render_csv(result) -> str`.

- [ ] Write deterministic-output tests, JSON Schema validation, CSV escaping/details encoding, safe output paths, and replacement behavior.
- [ ] Run tests; expect failure.
- [ ] Implement canonical serialization and atomic file replacement.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: generate JSON and CSV reports`.

### Task 18: Human-Readable Reporters

**Files:**
- Create: `src/un_schema_qa/reporters/markdown_report.py`
- Create: `src/un_schema_qa/reporters/html_report.py`
- Create: `src/un_schema_qa/templates/report.html.j2`
- Create: `tests/reporters/test_human_reports.py`

**Interfaces:**
- `render_markdown(result) -> str`.
- `render_html(result) -> str` produces self-contained escaped HTML.

- [ ] Write tests for summaries, grouped tables, empty results, HTML escaping, accessibility landmarks, embedded CSS, and absence of external URLs/scripts.
- [ ] Run tests; expect failure.
- [ ] Implement Markdown and Jinja2 HTML rendering.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: generate Markdown and HTML reports`.

### Task 19: Command-Line Interface

**Files:**
- Create: `src/un_schema_qa/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Implements all five commands and documented exit codes.
- `main()` is the console-script entry point.

- [ ] Write Typer CLI tests for help, version, list-checks, validate formats/output/exit codes, inspect-workbook, init profiles, overwrite protection, typed errors, and debug traces.
- [ ] Run tests; expect failure.
- [ ] Implement commands as thin API wrappers with no validation logic in CLI callbacks.
- [ ] Run tests; expect pass.
- [ ] Commit with `feat: add production command-line interface`.

### Task 20: Water Example Project

**Files:**
- Create: `examples/water/project.yml`
- Create: `examples/water/data/*.csv`
- Create: `examples/water/rules/engineering_rules.yml`
- Create: `examples/water/README.md`
- Create: `tests/integration/test_water_example.py`

**Interfaces:**
- Example includes source/target schemas, mappings, filters, domains, asset types, data references, rules, and known warning/error scenarios.

- [ ] Write integration test expecting exact status and stable finding-code counts.
- [ ] Run test; expect missing example failure.
- [ ] Create coherent synthetic water data and documented remediation walkthrough.
- [ ] Run test and generate all four reports in a temporary directory; expect pass.
- [ ] Commit with `docs: add complete water validation example`.

### Task 21: Wastewater and Stormwater Examples

**Files:**
- Create: `examples/wastewater/**`
- Create: `examples/stormwater/**`
- Create: `tests/integration/test_domain_examples.py`

**Interfaces:**
- Wastewater demonstrates gravity/force-main engineering rules, slope/invert context, terminals, and rule gaps.
- Stormwater demonstrates pipes/culverts/open channels/structures and dirty-area grouping.

- [ ] Write tests expecting exact statuses and finding-code counts for both projects.
- [ ] Run tests; expect missing examples.
- [ ] Create coherent synthetic projects, rules, and walkthroughs.
- [ ] Run both examples and all report formats; expect pass.
- [ ] Commit with `docs: add wastewater and stormwater examples`.

### Task 22: User and Technical Documentation

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/configuration.md`
- Create: `docs/input-formats.md`
- Create: `docs/validation-rules.md`
- Create: `docs/finding-codes.md`
- Create: `docs/python-api.md`
- Create: `docs/cli.md`
- Create: `docs/report-schema.md`
- Create: `tests/test_documentation.py`

**Interfaces:**
- Documentation must match public symbols, commands, aliases, finding codes, and JSON schema.

- [ ] Write consistency tests that extract finding codes and CLI commands and ensure every item is documented.
- [ ] Run tests; expect missing docs.
- [ ] Write the eight focused guides with runnable examples and cross-links.
- [ ] Run consistency tests; expect pass.
- [ ] Commit with `docs: document toolkit interfaces and formats`.

### Task 23: Project Governance and Release Documentation

**Files:**
- Create: `CHANGELOG.md`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `docs/tutorials/water.md`
- Create: `docs/tutorials/wastewater.md`
- Create: `docs/tutorials/stormwater.md`
- Modify: `README.md`
- Test: `tests/test_documentation.py`

**Interfaces:**
- README describes implemented V1 behavior only and links to all examples/guides.

- [ ] Extend documentation tests for links, version, install command, and removal of planned/future claims.
- [ ] Run tests; expect failure against the planning README.
- [ ] Write governance files, tutorials, changelog, and implementation-accurate README.
- [ ] Run documentation tests; expect pass.
- [ ] Commit with `docs: publish V1 user and contributor guides`.

### Task 24: CI, Quality Gates, and Release Hardening

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release.yml`
- Modify: `pyproject.toml`
- Create: `tests/integration/test_installed_package.py`

**Interfaces:**
- CI runs Ruff, mypy, pytest with 90% coverage, build, and metadata checks.
- Release workflow builds on version tags and uses trusted publishing configuration without stored credentials.

- [ ] Write installed-wheel smoke test covering imports, `version`, `list-checks`, and one example validation.
- [ ] Run full local checks and record any failures.
- [ ] Add CI/release workflows and tighten tool configuration until all checks pass.
- [ ] Build sdist/wheel, install wheel into a fresh virtual environment, run smoke test and all three examples.
- [ ] Run `ruff check .`, `ruff format --check .`, `mypy src`, `pytest --cov=un_schema_qa --cov-fail-under=90`, `python -m build`, and `twine check dist/*`; expect all pass.
- [ ] Commit with `release: harden utility network schema QA V1`.

### Task 25: Final V1 Acceptance and Tag-Ready State

**Files:**
- Modify only files required by acceptance failures.

**Interfaces:**
- Produces a clean, tag-ready `1.0.0` repository with no unsupported claims.

- [ ] Execute the full design-spec acceptance checklist in a fresh environment.
- [ ] Compare every README capability against a passing test or example and remove or implement discrepancies.
- [ ] Verify repository contains no placeholders, empty modules, generated reports, credentials, internal paths, or proprietary dependencies.
- [ ] Run all quality, build, install, and example commands again from a clean checkout.
- [ ] Commit any real acceptance corrections with a focused message; do not create an empty commit.
- [ ] Record final commit, check results, package artifacts, and remaining release action without pushing or tagging unless explicitly requested.
