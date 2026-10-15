
"""Paired baseline-versus-defense model evaluation runner.

All proposed actions are scored as data. No simulator tools are executed.
The model callable is injected by the caller; this module makes no provider
SDK or network calls.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.model_evaluation import (
    ModelOutputError,
    build_messages,
    parse_model_output,
)
from backend.app.model_scoring import aggregate_results, score_attempt


CONDITIONS = ("baseline", "defense")


def run_paired_evaluation(
    records: list[dict[str, Any]],
    model_callable: Callable[[list[dict[str, str]]], str],
) -> dict[str, Any]:
    """Evaluate each record under both conditions without executing actions.

    Invalid model outputs and callable errors are retained as failed attempts.
    """
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
                    f"Model callable error: {type(exc).__name__}: {exc}"
                )
                result["call_error"] = True
                attempts.append(result)
                continue

            result = score_attempt(record, condition, raw_output)
            result["call_error"] = False

            # Keep raw output for auditability, including malformed output.
            # Reports contain model responses; store them securely.
            result["raw_output"] = (
                raw_output if isinstance(raw_output, str) else repr(raw_output)
            )
            attempts.append(result)

    aggregate = aggregate_results(attempts)

    return {
        "report_schema_version": "1.0",
        "run_metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "scenario_count": len(records),
            "conditions": list(CONDITIONS),
            "expected_attempt_count": len(records) * len(CONDITIONS),
            "actual_attempt_count": len(attempts),
            "callable_error_count": callable_errors,
            "tool_execution_enabled": False,
            "dataset_review_status": "draft",
        },
        "limitations": [
            "Proposed actions are never executed.",
            "Task completion is a model self-report, not verified success.",
            "Invalid outputs are counted separately from valid outputs.",
            "Results apply only to the supplied scenarios and model callable.",
            "The harness supplies structured scenario fields; this does not "
            "by itself establish natural-language understanding robustness.",
            "Pilot records remain draft pending independent linguistic review.",
        ],
        "attempts": attempts,
        "aggregate": aggregate,
    }


def export_report(
    report: dict[str, Any],
    output_dir: str | Path,
    run_name: str = "paired_evaluation",
) -> tuple[Path, Path]:
    """Write a JSON audit report and a flat CSV of individual attempts."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    json_path = destination / f"{run_name}.json"
    csv_path = destination / f"{run_name}.csv"

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    attempts = report.get("attempts", [])
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

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(attempts)

    return json_path, csv_path
