# Field Mapping Semantic QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic metadata-level mapping QA for lifecycle status, owner, and elevation fields, with runnable examples and complete user documentation.

**Architecture:** Extend canonical field mapping rows with optional semantic metadata, parse it through the existing reader/loader pipeline, and run a new `field_semantics` validator beside the generic mapping and domain validators. Existing report models remain unchanged because semantic results use standard findings.

**Tech Stack:** Python 3.10+, Pydantic 2, Typer, pytest, Ruff, mypy, CSV/YAML fixtures, Markdown documentation.

## Global Constraints

- Do not connect to a live Utility Network, geodatabase, feature service, or ArcPy runtime.
- Do not read feature-level records or execute mapping expressions.
- Preserve backward compatibility: every new mapping column is optional and rows without `semantic_role` produce no semantic findings.
- Supported roles are exactly `lifecycle_status`, `owner`, and `elevation` after header-style normalization.
- Supported canonical elevation units are exactly `m`, `ft`, and `us_survey_ft`.
- Every implementation commit must be substantive and leave the test suite passing.
- Keep the package version at `1.0.0`; release versioning and PyPI publication are outside this change.

---

### Task 1: Model semantic field metadata

**Files:**
- Modify: `src/un_schema_qa/models/mapping.py`
- Create: `tests/models/test_mapping_models.py`

**Interfaces:**
- Consumes: Existing immutable `FieldMapping` Pydantic model.
- Produces: Optional string fields `semantic_role`, `source_unit`, `target_unit`, `source_vertical_datum`, `target_vertical_datum`, and `field_rationale`.

- [ ] **Step 1: Add a failing model test**

```python
from un_schema_qa.models import FieldMapping


def test_field_mapping_stores_semantic_qa_metadata() -> None:
    mapping = FieldMapping(
        source_field="elevation_ft",
        target_field="elevation_m",
        semantic_role="elevation",
        source_unit="us_survey_ft",
        target_unit="m",
        source_vertical_datum="NAVD88",
        target_vertical_datum="NAVD88",
        field_rationale="Convert source survey feet to metres.",
    )

    assert mapping.semantic_role == "elevation"
    assert mapping.source_unit == "us_survey_ft"
    assert mapping.target_unit == "m"
    assert mapping.source_vertical_datum == "NAVD88"
    assert mapping.target_vertical_datum == "NAVD88"
    assert mapping.field_rationale.startswith("Convert")
```

- [ ] **Step 2: Run the focused test and observe missing-field failure**

Run: `pytest tests/models/test_mapping_models.py -q`

Expected: failure because `FieldMapping` rejects the new keys.

- [ ] **Step 3: Add the six optional fields to `FieldMapping`**

```python
class FieldMapping(StrictModel):
    source_field: str | None = None
    target_field: str
    expression: str | None = None
    lookup: str | None = None
    default: Any = None
    semantic_role: str | None = None
    source_unit: str | None = None
    target_unit: str | None = None
    source_vertical_datum: str | None = None
    target_vertical_datum: str | None = None
    field_rationale: str | None = None
    location: SourceLocation | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Run model and full tests**

Run: `pytest tests/models/test_mapping_models.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/models/mapping.py tests/models/test_mapping_models.py
git commit -m "feat: model semantic field mapping metadata"
```

---

### Task 2: Parse semantic mapping columns and aliases

**Files:**
- Modify: `src/un_schema_qa/row_schemas.py`
- Modify: `src/un_schema_qa/loaders.py`
- Modify: `tests/test_loaders.py`
- Modify: `tests/test_normalization.py`

**Interfaces:**
- Consumes: Task 1 `FieldMapping` fields and existing `resolve_columns` behavior.
- Produces: Canonical metadata populated from CSV, TSV, JSON, YAML, XLSX, and XLSM mapping rows.

- [ ] **Step 1: Add failing alias and loader tests**

Add a mapping row using headers `QA Role`, `From Unit`, `To Unit`, `Source Datum`, `Target Datum`, and `Mapping Rationale`, then assert the canonical field values equal `elevation`, `ft`, `m`, `NAVD88`, `NAVD88`, and the supplied rationale.

- [ ] **Step 2: Run focused tests and observe missing values**

Run: `pytest tests/test_loaders.py tests/test_normalization.py -q`

Expected: the semantic values are absent.

- [ ] **Step 3: Add logical columns and aliases**

```python
"semantic_role": {"semantic_role", "qa_role", "field_role"},
"source_unit": {"source_unit", "from_unit"},
"target_unit": {"target_unit", "to_unit"},
"source_vertical_datum": {"source_vertical_datum", "source_datum"},
"target_vertical_datum": {"target_vertical_datum", "target_datum"},
"field_rationale": {"field_rationale", "mapping_rationale"},
```

Populate each value with `_text(_value(row, columns, name))` when constructing `FieldMapping`.

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/test_loaders.py tests/test_normalization.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/row_schemas.py src/un_schema_qa/loaders.py tests/test_loaders.py tests/test_normalization.py
git commit -m "feat: load semantic field mapping columns"
```

---

### Task 3: Register the field semantics validator

**Files:**
- Create: `src/un_schema_qa/validators/field_semantics.py`
- Modify: `src/un_schema_qa/validators/__init__.py`
- Modify: `src/un_schema_qa/engine.py`
- Modify: `src/un_schema_qa/config.py`
- Modify: `src/un_schema_qa/cli.py`
- Create: `tests/validators/test_field_semantics_validator.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `ValidationContext`, standard `finding()` helper, and semantic `FieldMapping` metadata.
- Produces: `FieldSemanticsValidator.name == "field_semantics"`, unknown-role and missing-rationale findings, default registry/config/CLI integration.

- [ ] **Step 1: Add failing registry, CLI, role, and rationale tests**

Test that `field_semantics` appears in `DEFAULT_CHECKS`, the registry, and `list-checks`; that `unsupported-role` emits `FIELD_SEMANTIC_ROLE_UNKNOWN`; and that a supported role without rationale emits `FIELD_SEMANTIC_RATIONALE_MISSING`.

- [ ] **Step 2: Run focused tests and observe missing validator failure**

Run: `pytest tests/validators/test_field_semantics_validator.py tests/test_config.py tests/test_cli.py -q`

Expected: import/registry/check-name failures.

- [ ] **Step 3: Implement shared validator behavior**

Create `FieldSemanticsValidator` with `required_inputs = ("mappings", "source_datasets", "target_datasets")`, normalize roles using `normalize_header`, skip empty roles, emit the two shared findings, resolve fields, and defer role-specific methods to later tasks. Register it after `MappingValidator`, add it to `DEFAULT_CHECKS`, and add this CLI description:

```python
"field_semantics": "Lifecycle, owner, elevation unit, datum, and rationale checks.",
```

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/validators/test_field_semantics_validator.py tests/test_config.py tests/test_cli.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/validators/field_semantics.py src/un_schema_qa/validators/__init__.py src/un_schema_qa/engine.py src/un_schema_qa/config.py src/un_schema_qa/cli.py tests/validators/test_field_semantics_validator.py tests/test_config.py tests/test_cli.py
git commit -m "feat: register semantic field mapping validator"
```

---

### Task 4: Validate lifecycle status semantics

**Files:**
- Modify: `src/un_schema_qa/validators/field_semantics.py`
- Modify: `tests/validators/test_field_semantics_validator.py`

**Interfaces:**
- Consumes: Resolved source and target `FieldSchema` objects for role `lifecycle_status`.
- Produces: `FIELD_LIFECYCLE_SOURCE_DOMAIN_MISSING` and `FIELD_LIFECYCLE_TARGET_DOMAIN_MISSING`.

- [ ] **Step 1: Add failing lifecycle tests**

Cover no domains, source-only domain, target-only domain, and both-domain success. Assert the role-specific codes and no duplicate generic domain code.

- [ ] **Step 2: Run focused tests and observe missing findings**

Run: `pytest tests/validators/test_field_semantics_validator.py -q`

Expected: lifecycle assertions fail.

- [ ] **Step 3: Implement lifecycle checks**

For resolved fields, emit the source code when `source_field.domain` is empty and the target code when `target_field.domain` is empty. Recommendations must instruct users to export/assign coded-value domains and document `target_code` crosswalks.

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/validators/test_field_semantics_validator.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/validators/field_semantics.py tests/validators/test_field_semantics_validator.py
git commit -m "feat: validate lifecycle status field mappings"
```

---

### Task 5: Validate owner semantics

**Files:**
- Modify: `src/un_schema_qa/validators/field_semantics.py`
- Modify: `tests/validators/test_field_semantics_validator.py`

**Interfaces:**
- Consumes: Resolved owner fields, data types, lengths, and domain references.
- Produces: `FIELD_OWNER_TYPE_INVALID`, `FIELD_OWNER_LENGTH_RISK`, and `FIELD_OWNER_DOMAIN_ASYMMETRIC`.

- [ ] **Step 1: Add failing owner tests**

Cover non-text source and target, source length greater than target length, exactly equal lengths, one-sided domain, two-sided domains, and lookup/expression mappings with rationale.

- [ ] **Step 2: Run focused tests and observe missing findings**

Run: `pytest tests/validators/test_field_semantics_validator.py -q`

Expected: owner assertions fail.

- [ ] **Step 3: Implement owner checks**

Emit one type finding per invalid side with `details={"side": side, "data_type": field.data_type}`. Emit length risk only when both lengths are known and source is greater. Emit domain asymmetry when exactly one field declares a domain.

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/validators/test_field_semantics_validator.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/validators/field_semantics.py tests/validators/test_field_semantics_validator.py
git commit -m "feat: validate owner field mappings"
```

---

### Task 6: Validate elevation types and units

**Files:**
- Modify: `src/un_schema_qa/validators/field_semantics.py`
- Modify: `tests/validators/test_field_semantics_validator.py`

**Interfaces:**
- Consumes: Elevation field types, unit metadata, and optional expression.
- Produces: Unit alias normalization and `FIELD_ELEVATION_TYPE_INVALID`, `FIELD_ELEVATION_UNIT_MISSING`, `FIELD_ELEVATION_UNIT_UNKNOWN`, and `FIELD_ELEVATION_CONVERSION_MISSING`.

- [ ] **Step 1: Add failing elevation type/unit tests**

Cover text fields, absent units, aliases for metres/feet/US survey feet, unsupported units, same-unit direct mapping, different units without expression, and different units with expression.

- [ ] **Step 2: Run focused tests and observe missing findings**

Run: `pytest tests/validators/test_field_semantics_validator.py -q`

Expected: elevation unit assertions fail.

- [ ] **Step 3: Implement numeric and unit checks**

Use numeric types `small_integer`, `integer`, `float`, and `double`. Normalize unit aliases to `m`, `ft`, or `us_survey_ft`. Only compare units when both normalize successfully. Require an expression when canonical units differ.

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/validators/test_field_semantics_validator.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/validators/field_semantics.py tests/validators/test_field_semantics_validator.py
git commit -m "feat: validate elevation units and conversions"
```

---

### Task 7: Validate elevation vertical datums

**Files:**
- Modify: `src/un_schema_qa/validators/field_semantics.py`
- Modify: `tests/validators/test_field_semantics_validator.py`

**Interfaces:**
- Consumes: Source/target vertical datum strings and optional expression.
- Produces: `FIELD_ELEVATION_DATUM_MISSING` and `FIELD_ELEVATION_DATUM_TRANSFORM_MISSING`.

- [ ] **Step 1: Add failing datum tests**

Cover each missing side, case-insensitive same datum, different datum without expression, and different datum with an expression and rationale.

- [ ] **Step 2: Run focused tests and observe missing findings**

Run: `pytest tests/validators/test_field_semantics_validator.py -q`

Expected: datum assertions fail.

- [ ] **Step 3: Implement datum checks**

Emit one missing-datum finding containing a `missing` list. Compare trimmed case-folded names only when both are supplied. Require `expression` when they differ.

- [ ] **Step 4: Run focused and full tests**

Run: `pytest tests/validators/test_field_semantics_validator.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/un_schema_qa/validators/field_semantics.py tests/validators/test_field_semantics_validator.py
git commit -m "feat: validate elevation vertical datum metadata"
```

---

### Task 8: Extend the runnable water example

**Files:**
- Modify: `examples/water/project.yml`
- Modify: `examples/water/data/source_schema.csv`
- Modify: `examples/water/data/target_schema.csv`
- Modify: `examples/water/data/source_domains.csv`
- Modify: `examples/water/data/target_domains.csv`
- Modify: `examples/water/data/mappings.csv`
- Modify: `examples/water/README.md`
- Modify: `docs/tutorials/water.md`
- Modify: `tests/integration/test_water_example.py`

**Interfaces:**
- Consumes: All semantic metadata and validator behavior from Tasks 1-7.
- Produces: A passing synthetic project demonstrating lifecycle crosswalks, owner mapping, and survey-foot-to-metre elevation conversion.

- [ ] **Step 1: Update the integration assertion first**

Require `field_semantics` in the executed validator tuple and assert no finding code starts with `FIELD_`.

- [ ] **Step 2: Run the water integration test and observe failure**

Run: `pytest tests/integration/test_water_example.py -q`

Expected: `field_semantics` is not enabled in the example.

- [ ] **Step 3: Add complete synthetic metadata**

Add source fields `owner_name` (text length 100) and `elevation_ft` (double), assign `LegacyLifecycle` to source `lifecycle_status`, and add corresponding target fields `owner` (text length 128), `elevation` (double), and `lifecycle_status` with `TargetLifecycle`. Add source lifecycle codes `Active`, `Inactive`, and `Abandoned` with target codes `1`, `2`, and `3`; add matching target codes. Add semantic mapping rows to both water mapping partitions. Elevation rows declare `us_survey_ft` to `m`, `NAVD88` to `NAVD88`, an expression, and rationale.

- [ ] **Step 4: Enable the validator and document the example**

Add `field_semantics` after `mapping` in `project.yml`. Explain all three mappings and the non-execution limitation in the example README and tutorial.

- [ ] **Step 5: Run example and full tests**

Run: `pytest tests/integration/test_water_example.py -q && pytest -q`

Expected: all tests pass and the existing finding counter remains unchanged.

- [ ] **Step 6: Commit**

```bash
git add examples/water docs/tutorials/water.md tests/integration/test_water_example.py
git commit -m "examples: demonstrate semantic field mapping QA"
```

---

### Task 9: Document inputs, checks, and findings

**Files:**
- Modify: `docs/configuration.md`
- Modify: `docs/input-formats.md`
- Modify: `docs/validation-rules.md`
- Modify: `docs/finding-codes.md`
- Modify: `tests/test_documentation.py`

**Interfaces:**
- Consumes: Stable input columns, validator name, and finding codes.
- Produces: Complete reference documentation enforced by documentation tests.

- [ ] **Step 1: Strengthen documentation tests**

Add `FIELD` to the finding-prefix expression and assert the input-format guide includes every semantic column and role.

- [ ] **Step 2: Run documentation tests and observe catalog failures**

Run: `pytest tests/test_documentation.py -q`

Expected: new finding codes are missing from the catalog.

- [ ] **Step 3: Document the full public contract**

Document role behavior, severity, aliases, unit names, datum comparison, domain/crosswalk delegation, optional compatibility, manifest enablement, and expression non-execution. Add every `FIELD_*` code to the catalog.

- [ ] **Step 4: Run documentation and full tests**

Run: `pytest tests/test_documentation.py -q && pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add docs/configuration.md docs/input-formats.md docs/validation-rules.md docs/finding-codes.md tests/test_documentation.py
git commit -m "docs: catalog semantic field mapping QA"
```

---

### Task 10: Publish README workflow and changelog entry

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_documentation.py`

**Interfaces:**
- Consumes: Complete implementation and runnable water example.
- Produces: User-facing project-manifest explanation, field mapping CSV example, commands, expected QA table, limitations, and an Unreleased changelog entry.

- [ ] **Step 1: Add failing README content assertions**

Assert the README contains `semantic_role`, `lifecycle_status`, `owner`, `elevation`, `source_vertical_datum`, `target_vertical_datum`, `field_semantics`, and language distinguishing real exported metadata from live/feature-level data.

- [ ] **Step 2: Run documentation tests and observe missing README content**

Run: `pytest tests/test_documentation.py -q`

Expected: the new README assertions fail.

- [ ] **Step 3: Rewrite the usage sections**

Clarify the manifest role, show the required real exported artifacts, add a compact but complete mapping CSV example for all three roles, explain each QA outcome, show `validate` and targeted `--check field_semantics` commands, and state that expressions and record values are not evaluated.

- [ ] **Step 4: Add the changelog entry**

Add an `Unreleased` section covering semantic mapping metadata, the new validator, the expanded water example, and the documentation.

- [ ] **Step 5: Run all quality gates**

Run:

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=un_schema_qa --cov-fail-under=90
git diff --check
```

Expected: all commands pass and coverage remains at least 90%.

- [ ] **Step 6: Commit**

```bash
git add README.md CHANGELOG.md tests/test_documentation.py
git commit -m "docs: explain semantic Utility Network field QA"
```

---

## Final Verification and Integration

- [ ] Confirm the feature branch contains at least ten substantive implementation commits after the approved design commit.
- [ ] Confirm only intended source, tests, examples, and documentation files changed.
- [ ] Run Ruff formatting/checks, mypy, the full branch-coverage test gate, package build, and Twine metadata validation in a fresh environment.
- [ ] Verify all three existing examples still produce their documented status and finding counters.
- [ ] Fast-forward merge into `main`, repeat the full test gate, push `main`, verify the remote SHA, and wait for all GitHub Actions jobs.
- [ ] Do not create a new tag or publish PyPI without a separate release instruction.
