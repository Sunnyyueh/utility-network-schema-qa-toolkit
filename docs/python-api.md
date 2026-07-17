# Python API

The public package exports `load_project`, `validate_project`, `write_reports`, and `__version__`.

```python
from pathlib import Path
from un_schema_qa import load_project, validate_project, write_reports

manifest = Path("examples/water/project.yml")
project = load_project(manifest)
result = validate_project(project, checks=("schema", "mapping", "filters"))
paths = write_reports(result, Path("reports"), formats=("json", "html"))
```

## `load_project`

`load_project(path: Path | str) -> ProjectData` parses the manifest and every configured input into immutable canonical models. Configuration and format problems raise typed subclasses of `ToolkitError`.

## `validate_project`

`validate_project(project_or_path, *, checks=None) -> ValidationResult` accepts a loaded `ProjectData` or manifest path. Passing a path applies manifest-enabled checks and severity overrides. Passing a model uses default checks unless `checks` is supplied.

The returned result contains schema/toolkit versions, project name, SHA-256 input fingerprint, validators actually executed, sorted findings, counts, and aggregate status. Optional inventory validators are omitted from `validators` when their input is absent.

## `write_reports`

`write_reports(result, output_dir=None, *, formats=(...)) -> dict[str, Path]` creates fixed report filenames using atomic replacement. Supported formats are JSON, CSV, Markdown, and HTML.

## Lower-level extension API

Advanced integrations may import `ValidatorRegistry`, `build_default_registry`, and `run_validation` from `un_schema_qa.engine`, or `ValidationContext` and validator classes from `un_schema_qa.validators`. These are useful for adding organization-specific checks without changing input files.

The API does not perform network requests, evaluate input expressions, or mutate the loaded project.

