"""Approximate, evidence-based English transcript analysis."""

from .analyzer import Analyzer, analyze
from .contract import RESULT_SCHEMA_PATH, SCHEMA_VERSION

__all__ = ["Analyzer", "analyze", "SCHEMA_VERSION", "RESULT_SCHEMA_PATH"]
