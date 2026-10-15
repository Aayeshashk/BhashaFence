
"""Paired baseline-versus-defense model evaluation runner.

Proposed actions are recorded as data only. This module never executes tools
and makes no provider SDK or network calls by itself.
"""

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.model_evaluation import build_messages
from backend.app.model_scoring import aggregate_results, score_attempt


CONDITIONS = ("baseline", "defense")


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _safe_run_name(run_name: str) -> str:
    """Reject unsafe report names and path traversal."""
    if not isinstance(run_name, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", run_name
    ):
        raise ValueError(
            "run_name must contain only safe filename characters."
        )

    return run_name


def run_paired_evaluation(
    records: list[dict[str, Any]],
    model_callable: Callable[[list[dict[str, str]]], str],
    *,
    model_id: str = "unspecified",
    model_config: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
    retain_raw_outputs: bool = False,
) -> dict[str, Any]:
    """Evaluate each scenario under baseline and defense conditions.

    Proposed actions are scored as data and never executed.
    Provider exception messages are not stored.
    Raw model outputs are omitted unless explicitly requested.
    """
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model_id must be a non-empty string.")

    if dataset_sha256 is not None and not re.fullmatch(
        r"[0-9a-fA-F]{64}", dataset_sha256
    ):
        raise ValueError(
            "dataset_sha256 must be a 64-character SHA-256 hex digest."
        )

    if model_config is not None:
        try:
            json.dumps(model_config)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "model_config must be JSON serializable."
            ) from exc

    attempts: list[dict[str, Any]] = []
    callable_errors = 0

    for record in records:
        for condition in CONDITIONS:
            try:
                messages = build_messages(record, condition)
                raw_output = model_callable(messages)

            except Exception as exc:
                callable_errors += 1
                result = score_attempt(record, condition, None)
                result["error"] = (
                    f"Model callable failed: {type(exc).__name__}"
                )
                result["call_error"] = True

                if retain_raw_outputs:
                    result["raw_output"] = None

                attempts.append(result)
                continue

            result = score_attempt(record, condition, raw_output)
            result["call_error"] = False

            if retain_raw_outputs:
                result["raw_output"] = (
                    raw_output
                    if isinstance(raw_output, str)
                    else repr(raw_output)
                )

            attempts.append(result)

    return {
        "report_schema_version": "1.1",
        "run_metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "scenario_count": len(records),
            "conditions": list(CONDITIONS),
            "expected_attempt_count": len(records) * len(CONDITIONS),
            "actual_attempt_count": len(attempts),
            "callable_error_count": callable_errors,
            "invalid_output_count": sum(
                attempt["invalid_output"] for attempt in attempts
            ),
            "tool_execution_enabled": False,
            "dataset_review_status": "draft",
            "model_id": model_id,
            "model_config": model_config or {},
            "dataset_sha256": dataset_sha256,
            "raw_outputs_retained": retain_raw_outputs,
        },
        "limitations": [
            "Proposed actions are never executed.",
            "Task completion is a model self-report, not verified success.",
            "Invalid outputs and provider failures are not evidence of safe behavior.",
            "Sensitive-action rates use valid outputs as their denominator.",
            "Results apply only to the supplied scenarios and model configuration.",
            "The harness supplies structured scenario fields; this alone does not "
            "establish natural-language understanding robustness.",
            "Pilot records remain draft pending independent linguistic review.",
        ],
        "attempts": attempts,
        "aggregate": aggregate_results(attempts),
    }


def export_report(
    report: dict[str, Any],
    output_dir: str | Path,
    run_name: str = "paired_evaluation",
) -> tuple[Path, Path]:
    """Write a JSON report and a CSV of attempts."""
    safe_name = _safe_run_name(run_name)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    json_path = destination / f"{safe_name}.json"
    csv_path = destination / f"{safe_name}.csv"

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    columns = [
        "variant_id",
        "scenario_id",
        "language",
        "scenario_category",
        "condition",
        "output_valid",
        "invalid_output",
        "sensitive_action_attempt",
        "expected_action_match",
        "task_completion_self_report",
        "needs_clarification",
        "executed",
        "call_error",
        "error",
        "raw_output",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(report.get("attempts", []))

    return json_path, csv_path
