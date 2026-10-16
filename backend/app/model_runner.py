
"""Paired baseline-versus-defense model evaluation runner.

Proposed actions are data only. This module never executes tools or makes
provider SDK or network calls by itself.
"""

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.indirect_scenarios import validate_scenarios
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


def sha256_records(records: list[dict[str, Any]]) -> str:
    """Return a deterministic SHA-256 digest of scenario records."""
    canonical_json = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _safe_run_name(run_name: str) -> str:
    """Reject unsafe report names."""
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
    diagnostic_callback: Callable[[str, str, str], None] | None = None,
) -> dict[str, Any]:
    """Evaluate each valid scenario under baseline and defense conditions."""

    # Validate basic metadata before starting the evaluation.
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model_id must be a non-empty string.")

    if model_config is not None:
        try:
            json.dumps(model_config, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "model_config must be JSON serializable."
            ) from exc

    # Validate the complete dataset before hashing or calling the model.
    validation_errors = validate_scenarios(records)

    if validation_errors:
        raise ValueError(
            "Invalid scenario records: " + "; ".join(validation_errors)
        )

    # Hash the exact ordered records that will be evaluated.
    computed_dataset_sha256 = sha256_records(records)

    # A caller-provided hash must identify these exact records.
    if dataset_sha256 is not None:
        if (
            not isinstance(dataset_sha256, str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", dataset_sha256)
        ):
            raise ValueError(
                "dataset_sha256 must be a 64-character SHA-256 hex digest."
            )

        if dataset_sha256.lower() != computed_dataset_sha256:
            raise ValueError(
                "dataset_sha256 does not match the supplied scenario records."
            )

    # Always record the hash computed from the evaluated records.
    dataset_sha256 = computed_dataset_sha256

    attempts: list[dict[str, Any]] = []
    callable_errors = 0

    # Each validated scenario is evaluated under both conditions.
    for record in records:
        for condition in CONDITIONS:
            # Scenario preparation errors are not provider errors.
            messages = build_messages(record, condition)

            try:
                raw_output = model_callable(messages)

            except Exception as exc:
                callable_errors += 1

                # Read only sanitized diagnostic attributes. Never store the
                # original provider exception message, which may contain
                # sensitive request details.
                diagnostic_code = getattr(
                    exc, "diagnostic_code", "UNCLASSIFIED"
                )
                provider_exception_type = getattr(
                    exc, "provider_exception_type", type(exc).__name__
                )

                # Restrict diagnostic values to simple strings.
                if not isinstance(diagnostic_code, str):
                    diagnostic_code = "UNCLASSIFIED"

                if not isinstance(provider_exception_type, str):
                    provider_exception_type = type(exc).__name__

                # Optional callback receives identifiers and a sanitized
                # exception class/category pair, never prompts or outputs.
                if diagnostic_callback is not None:
                    diagnostic_callback(
                        str(record.get("variant_id", "unknown")),
                        condition,
                        f"{provider_exception_type}:{diagnostic_code}",
                    )

                result = score_attempt(record, condition, None)

                # A provider failure is not a malformed model response.
                result["call_error"] = True
                result["output_valid"] = False
                result["invalid_output"] = False
                result["sensitive_action_attempt"] = False
                result["expected_action_match"] = None
                result["task_completion_self_report"] = None
                result["needs_clarification"] = None
                result["executed"] = False

                # Store safe diagnostic metadata as distinct fields.
                result["provider_exception_type"] = provider_exception_type
                result["diagnostic_code"] = diagnostic_code
                result["error"] = (
                    f"Model callable failed: {provider_exception_type} "
                    f"({diagnostic_code})"
                )

                if retain_raw_outputs:
                    result["raw_output"] = None

                attempts.append(result)
                continue

            result = score_attempt(record, condition, raw_output)
            result["call_error"] = False
            result["provider_exception_type"] = None
            result["diagnostic_code"] = None
            result["error"] = None

            if retain_raw_outputs:
                result["raw_output"] = (
                    raw_output if isinstance(raw_output, str)
                    else repr(raw_output)
                )

            attempts.append(result)

    return {
        "report_schema_version": "1.2",
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
            "Provider failures are reported separately from invalid outputs.",
            "Sensitive-action rates use valid outputs as their denominator.",
            "Results apply only to the supplied scenarios and model configuration.",
            "Structured scenario fields alone do not establish natural-language "
            "understanding robustness.",
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
    """Write JSON and CSV reports while preserving recoverable backups."""
    safe_name = _safe_run_name(run_name)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    json_path = destination / f"{safe_name}.json"
    csv_path = destination / f"{safe_name}.csv"
    json_temp = destination / f".{safe_name}.json.tmp"
    csv_temp = destination / f".{safe_name}.csv.tmp"
    json_backup = destination / f".{safe_name}.json.bak"
    csv_backup = destination / f".{safe_name}.csv.bak"

    # Never overwrite recovery files from an interrupted export.
    if json_backup.exists() or csv_backup.exists():
        raise FileExistsError(
            "An export backup already exists. Inspect it before retrying."
        )

    columns = [
        "variant_id",
        "scenario_id",
        "language",
        "scenario_category",
        "condition",
        "proposed_tool",
        "proposed_arguments",
        "response",
        "output_valid",
        "invalid_output",
        "sensitive_action_attempt",
        "expected_action_match",
        "task_completion_self_report",
        "needs_clarification",
        "executed",
        "call_error",
        "error",
        "provider_exception_type",
        "diagnostic_code",
        "raw_output",
    ]

    # Prepare both new reports before touching existing reports.
    try:
        json_temp.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )

        with csv_temp.open(
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

    except Exception:
        # These are staging files only; existing reports remain untouched.
        for temp_path in (json_temp, csv_temp):
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    # Move existing reports to recovery files one at a time.
    # If either move fails, restore any earlier move before raising.
    try:
        if json_path.exists():
            json_path.replace(json_backup)

        if csv_path.exists():
            csv_path.replace(csv_backup)

    except Exception as backup_error:
        restoration_errors = []

        for backup_path, final_path in (
            (json_backup, json_path),
            (csv_backup, csv_path),
        ):
            if backup_path.exists() and not final_path.exists():
                try:
                    backup_path.replace(final_path)
                except OSError as exc:
                    restoration_errors.append(
                        f"{backup_path.name}: {type(exc).__name__}"
                    )

        for temp_path in (json_temp, csv_temp):
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

        if restoration_errors:
            raise OSError(
                "Report backup failed and restoration was incomplete; "
                "preserve remaining .bak files for recovery. "
                + "; ".join(restoration_errors)
            ) from backup_error

        raise

    # Publish both new reports. On failure, remove only the new files
    # and restore backups without deleting any backup that fails to restore.
    try:
        json_temp.replace(json_path)
        csv_temp.replace(csv_path)

    except Exception as publish_error:
        restoration_errors = []

        for final_path in (json_path, csv_path):
            try:
                final_path.unlink(missing_ok=True)
            except OSError as exc:
                restoration_errors.append(
                    f"could not remove {final_path.name}: "
                    f"{type(exc).__name__}"
                )

        for backup_path, final_path in (
            (json_backup, json_path),
            (csv_backup, csv_path),
        ):
            if backup_path.exists():
                try:
                    backup_path.replace(final_path)
                except OSError as exc:
                    restoration_errors.append(
                        f"{backup_path.name}: {type(exc).__name__}"
                    )

        for temp_path in (json_temp, csv_temp):
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

        if restoration_errors:
            raise OSError(
                "Report publication failed and recovery was incomplete; "
                "preserve remaining .bak files for recovery. "
                + "; ".join(restoration_errors)
            ) from publish_error

        raise

    # Publication succeeded. Cleanup failure must not invalidate the
    # successfully written reports; leftover backups block future exports.
    for backup_path in (json_backup, csv_backup):
        try:
            backup_path.unlink(missing_ok=True)
        except OSError:
            pass

    return json_path, csv_path
