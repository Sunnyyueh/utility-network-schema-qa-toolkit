"""Shared enums and source metadata."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model used by all canonical toolkit data."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class Severity(str, Enum):
    """Finding severity ordered from informational to blocking."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    @property
    def rank(self) -> int:
        return {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}[self]


class RunStatus(str, Enum):
    """Overall result for a validation run."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class SourceLocation(StrictModel):
    """Location of a value in an input artifact."""

    path: str
    sheet: str | None = None
    row: int | None = Field(default=None, ge=1)
    column: str | None = None
