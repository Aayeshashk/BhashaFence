
"""Run a two-call Gemini diagnostic without executing proposed tools."""

import getpass
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from google import genai

from backend.app.gemini_adapter import (
    DEFAULT_MODEL,
    create_gemini_callable,
)
from backend.app.indirect_scenarios import validate_scenarios
from backend.app.model_runner import (
    export_report,
    run_paired_evaluation,
    sha256_records,
)

DATASET_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "processed"
    / "indirect_injection"
    / "pilot_scenarios.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "indirect_injection"
    / "gemini_targeted_diagnostic"
)


def safe_diagnostic(variant_id, condition, diagnostic):
    """Print diagnostic identifiers without provider response contents."""
    print(
        "[PROVIDER ERROR]",
        f"scenario={variant_id}",
        f"condition={condition}",
        f"diagnostic={diagnostic}",
    )


def main():
    try:
        records = json.loads(
            DATASET_PATH.read_text(encoding="utf-8")
        )
    except Exception as exc:
        print("Diagnostic setup failed while loading the dataset.")
        print("Exception type:", type(exc).__name__)
        print("Error details withheld.")
        return 1

    if not isinstance(records, list):
        print("Diagnostic aborted: dataset must be a JSON list.")
        return 1

    errors = validate_scenarios(records)
    if errors:
        print("Diagnostic aborted: dataset validation failed.")
        for error in errors:
            print("-", error)
        return 1

    selected = [
        record
        for record in records
        if record.get("variant_id") == "S3-en"
    ]

    if len(selected) != 1:
        print(
            "Diagnostic aborted: expected exactly one S3-en record; "
            f"found {len(selected)}."
        )
        return 1

    print("Model:", DEFAULT_MODEL)
    print("Selected scenario: S3-en")
    print("Planned calls: 2 (baseline and defense)")
    print("Tool execution: DISABLED")
    print("Raw output retention: DISABLED")
    print("Output directory:", OUTPUT_DIR)

    api_key = getpass.getpass(
        "Gemini API key (input hidden): "
    ).strip()

    if not api_key:
        print("Diagnostic aborted: no API key provided.")
        return 1

    client = None
    report = None
    setup_failed = False

    try:
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        setup_failed = True
        print("Gemini client initialization failed.")
        print("Exception type:", type(exc).__name__)
        print("Error details withheld.")
    finally:
        # This removes the local reference; it is not secure memory erasure.
        del api_key

    if setup_failed or client is None:
        return 1

    try:
        model_callable = create_gemini_callable(
            model=DEFAULT_MODEL,
            client=client,
        )

        report = run_paired_evaluation(
            selected,
            model_callable,
            model_id=DEFAULT_MODEL,
            model_config={
                "provider": "Google Gemini API",
                "selected_scenarios": 1,
                "conditions": ["baseline", "defense"],
                "tool_execution_enabled": False,
                "retain_raw_outputs": False,
                "purpose": "targeted_provider_diagnostic",
            },
            dataset_sha256=sha256_records(selected),
            retain_raw_outputs=False,
            diagnostic_callback=safe_diagnostic,
        )

    except Exception as exc:
        print("Diagnostic evaluation failed.")
        print("Exception type:", type(exc).__name__)
        print("Error details withheld.")
        return 1

    finally:
        try:
            client.close()
        except Exception:
            print("Warning: Gemini client cleanup failed.")

    # Export after client cleanup. A cleanup warning does not discard
    # an evaluation report that was successfully produced.
    try:
        json_path, csv_path = export_report(
            report,
            OUTPUT_DIR,
            run_name="s3_en_paired_diagnostic",
        )
    except Exception as exc:
        print("Diagnostic report export failed.")
        print("Exception type:", type(exc).__name__)
        print("Error details withheld.")
        return 1

    attempts = report.get("attempts", [])

    print("\nDIAGNOSTIC SUMMARY")
    print("Attempts:", len(attempts))
    print(
        "Provider errors:",
        sum(a.get("call_error") is True for a in attempts),
    )
    print(
        "Invalid outputs:",
        sum(
            a.get("invalid_output") is True
            and a.get("call_error") is not True
            for a in attempts
        ),
    )

    for attempt in attempts:
        print(
            attempt.get("scenario_id"),
            attempt.get("condition"),
            "provider_exception_type=",
            attempt.get("provider_exception_type"),
            "diagnostic_code=",
            attempt.get("diagnostic_code"),
        )

    print("JSON report:", json_path)
    print("CSV report:", csv_path)
    print("Executed tool actions: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
