"""Stable public Python API."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .config import load_config
from .engine import run_validation
from .loaders import load_project_data
from .models import ProjectData, ValidationResult


def load_project(path: Path | str) -> ProjectData:
    """Load a project manifest and all configured QA inputs."""

    return load_project_data(load_config(path))


def validate_project(
    project_or_path: ProjectData | Path | str,
    *,
    checks: Sequence[str] | None = None,
) -> ValidationResult:
    """Validate a loaded project or a project manifest path."""

    if isinstance(project_or_path, ProjectData):
        return run_validation(project_or_path, checks=checks)
    config = load_config(project_or_path)
    project = load_project_data(config)
    return run_validation(project, config=config, checks=checks)
