# Contributing

Issues, focused bug fixes, documentation improvements, new input aliases, and new validators are welcome.

## Development setup

```bash
git clone https://github.com/Sunnyyueh/utility-network-schema-qa-toolkit.git
cd utility-network-schema-qa-toolkit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows, activate with `.venv\Scripts\activate`.

## Working agreement

1. Open or reference an issue for material behavior changes.
2. Keep each change focused and include tests that fail before the implementation.
3. Preserve stable Finding codes unless the semantic meaning truly changes.
4. Update models, aliases, loaders, documentation, and examples together when adding input fields.
5. Do not add execution of user SQL, Arcade, Python, or arbitrary templates.
6. Use synthetic data in tests and examples.

Run before submitting:

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=un_schema_qa --cov-fail-under=90
python -m build
twine check dist/*
```

Pull requests should explain the user-visible behavior, validation evidence, and any report-schema compatibility impact. By contributing, you agree that your contribution is provided under the repository's MIT License.

