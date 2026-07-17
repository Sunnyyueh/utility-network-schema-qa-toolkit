"""Canonical JSON report rendering."""

from __future__ import annotations

import json

from un_schema_qa.models import ValidationResult


def render_json(result: ValidationResult) -> str:
    """Render stable, human-diffable canonical JSON."""

    payload = result.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
