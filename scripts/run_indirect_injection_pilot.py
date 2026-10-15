
"""Run the draft indirect-injection pilot with a deterministic test double.

No external model, network connection, or simulator tool is used.
All proposed actions are scored as data and are never executed.
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.indirect_scenarios import validate_scenarios
from backend.app.model_runner import export_report, run_paired_evaluation
from scripts.audit_indirect_injection_pilot import audit_dataset


DATASET_PATH = (
    ROOT / "dataset" / "processed" / "indirect_injection"
    / "pilot_scenarios.json"
)
OUTPUT_DIR = ROOT / "artifacts" / "indirect_injection" / "integration_run"


def deterministic_test_double(messages: list[dict[str, str]]) -> str:
    """Return a fixed valid response to test plumbing, not model security."""
    return json.dumps({
        "action": {"type": "no_action"},
        "task_completed": False,
        "needs_clarification": True,
        "response": "Deterministic integration-test response.",
    })


def main() -> None:
    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found: {DATASET_PATH}")

    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    schema_errors = validate_scenarios(records)
    if schema_errors:
        for error in schema_errors:
            print(f"SCHEMA ERROR: {error}")
        raise SystemExit("Schema validation failed; evaluation not run.")

    audit = audit_dataset(records)
    if not audit["passed"]:
        for error in audit["errors"]:
            print(f"AUDIT ERROR: {error}")
        raise SystemExit("Dataset audit failed; evaluation not run.")

    if any(record.get("review_status") != "draft" for record in records):
        raise SystemExit("Expected pilot records to remain draft.")

    report = run_paired_evaluation(records, deterministic_test_double)

    expected_attempts = len(records) * 2
    actual_attempts = len(report["attempts"])
    if actual_attempts != expected_attempts:
        raise SystemExit(
            f"Expected {expected_attempts} attempts; found {actual_attempts}."
        )

    condition_counts = Counter(
        attempt["condition"] for attempt in report["attempts"]
    )
    language_counts = Counter(
        attempt["language"] for attempt in report["attempts"]
    )

    if condition_counts != Counter({"baseline": len(records), "defense": len(records)}):
        raise SystemExit(f"Unexpected condition counts: {condition_counts}")

    expected_languages = {"en", "hi", "mr", "code_mixed"}
    if set(language_counts) != expected_languages:
        raise SystemExit(f"Unexpected language coverage: {language_counts}")

    if any(attempt.get("executed") is not False for attempt in report["attempts"]):
        raise SystemExit("Safety check failed: an attempt is marked executed.")

    report["run_metadata"]["evaluation_type"] = (
        "deterministic_pipeline_integration_test"
    )
    report["run_metadata"]["model_used"] = None
    report["run_metadata"]["dataset_path"] = str(
        DATASET_PATH.relative_to(ROOT)
    )
    report["run_metadata"]["source_dataset_audit_passed"] = audit["passed"]
    report["run_metadata"]["schema_validation_passed"] = True
    report["run_metadata"]["condition_counts"] = dict(condition_counts)
    report["run_metadata"]["language_attempt_counts"] = dict(language_counts)

    report["limitations"].append(
        "The deterministic test double does not measure model behavior, "
        "prompt-injection resistance, or translation quality."
    )

    json_path, csv_path = export_report(
        report,
        OUTPUT_DIR,
        "pilot_integration",
    )

    print(f"Dataset records: {len(records)}")
    print(f"Schema validation: PASSED")
    print(f"Structural audit: PASSED")
    print(f"Evaluation attempts: {actual_attempts}")
    print(f"Condition counts: {dict(condition_counts)}")
    print(f"Language attempt counts: {dict(language_counts)}")
    print("Tool execution: DISABLED")
    print("Real model calls: NONE")
    print(f"JSON report: {json_path.relative_to(ROOT)}")
    print(f"CSV report: {csv_path.relative_to(ROOT)}")
    print("Integration validation: PASSED")


if __name__ == "__main__":
    main()
