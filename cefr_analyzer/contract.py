"""Public response contract metadata; results remain ordinary dictionaries."""

from pathlib import Path

SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_PATH = Path(__file__).with_name("data") / "result.schema.json"
