from __future__ import annotations

import json
from pathlib import Path

from multinode_diag.schema_val import validate_artifact


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schema"
    / "benchmark_artifact_schema.json"
)

VALID_SAMPLE = (
    PROJECT_ROOT
    / "artifacts"
    / "examples"
    / "aws-g4dn-pp2-sample.json"
)


def test_sample_artifact_is_valid() -> None:
    assert validate_artifact(VALID_SAMPLE, SCHEMA_PATH) == []


def test_missing_parallelism_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(
        VALID_SAMPLE.read_text(encoding="utf-8")
    )
    payload.pop("parallelism")

    artifact = tmp_path / "invalid.json"
    artifact.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    errors = validate_artifact(
        artifact,
        SCHEMA_PATH,
    )

    assert errors
    assert any(
        "parallelism" in error
        for error in errors
    )


def test_invalid_pipeline_parallel_size_is_rejected(
    tmp_path: Path,
) -> None:
    payload = json.loads(
        VALID_SAMPLE.read_text(encoding="utf-8")
    )

    payload["parallelism"]["pipeline_parallel_size"] = 0

    artifact = tmp_path / "invalid-pp.json"
    artifact.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    errors = validate_artifact(
        artifact,
        SCHEMA_PATH,
    )

    assert errors
    assert any(
        "pipeline_parallel_size" in error
        for error in errors
    )
