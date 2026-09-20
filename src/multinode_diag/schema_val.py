"""Validate multi-node vLLM benchmark artifacts against the project schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schema" / "benchmark_artifact_schema.json"


class ArtifactValidationError(ValueError):
    """Raised when a benchmark artifact does not satisfy the JSON schema."""


def load_json(path: Path) -> Any:
    """Load a JSON document from disk."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ArtifactValidationError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactValidationError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def format_error_path(error: Any) -> str:
    """Return a human-readable JSON path for a validation error."""
    if not error.absolute_path:
        return "$"

    parts: list[str] = ["$"]

    for component in error.absolute_path:
        if isinstance(component, int):
            parts.append(f"[{component}]")
        else:
            parts.append(f".{component}")

    return "".join(parts)


def validate_artifact(
    artifact_path: Path,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> list[str]:
    """Validate an artifact and return all schema errors.

    An empty list means the artifact is valid.
    """
    schema = load_json(schema_path)
    artifact = load_json(artifact_path)

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ArtifactValidationError(
            f"Project schema is invalid: {exc.message}"
        ) from exc

    validator = Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )

    errors = sorted(
        validator.iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )

    return [
        f"{format_error_path(error)}: {error.message}"
        for error in errors
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a multi-node vLLM benchmark artifact."
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the benchmark artifact JSON file.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"JSON schema path (default: {DEFAULT_SCHEMA_PATH}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        errors = validate_artifact(args.file, args.schema)
    except ArtifactValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(
            f"INVALID: {args.file} failed validation with "
            f"{len(errors)} error(s):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"VALID: {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
