"""Structured input readers."""

from .base import TabularRows
from .registry import read_rows

__all__ = ["TabularRows", "read_rows"]
