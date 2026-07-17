"""Reader-neutral table contract."""

from __future__ import annotations

from typing import Any

from pydantic import model_validator

from un_schema_qa.models import SourceLocation
from un_schema_qa.models.common import StrictModel


class TabularRows(StrictModel):
    headers: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    locations: tuple[SourceLocation, ...]

    @model_validator(mode="after")
    def locations_match_rows(self) -> TabularRows:
        if len(self.rows) != len(self.locations):
            raise ValueError("each input row must have one source location")
        return self
