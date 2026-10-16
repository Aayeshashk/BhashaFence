import getpass
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.gemini_adapter import (
    DEFAULT_MODEL,
    create_gemini_callable,
)

from backend.app.model_runner import (
    export_report,
    run_paired_evaluation,
    sha256_records,
)

from backend.app.indirect_scenarios import validate_scenarios


DATASET_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "processed"
    / "indirect_injection"
    / "pilot_scenarios.json"
)

# Keep the earlier four-call pilot completely separate.
OUTPUT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "indirect_injection"
    / "gemini_multilingual_pilot"
)

EXPECTED_SCENARIOS = 16
EXPECTED_LANGUAGES = {"en", "hi", "mr", "code_mixed"}
EXPECTED_CALLS = EXPECTED_SCENARIOS * 2


def safe_diagnostic(variant_id, condition, exception_type):
    """Print minimal diagnostic metadata without sensitive content."""
    print(
        "[PROVIDER ERROR] "
        f"scenario={variant_id} "
        f"condition={condition} "
        f"exception_type={exception_type}"
    )


def main():
    # 1. Confirm the source dataset exists.
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Pilot dataset not found: {DATASET_PATH}"
        )

    # 2. Load and validate the original dataset.
    records = json.loads(
        DATASET_PATH.read_text(encoding="utf-8")
    )

    errors = validate_scenarios(records)

    if errors:
        raise ValueError(
            "Dataset validation failed:\n"
            + "\n".join(errors)
        )

    # 3. Select every record without modifying the dataset.
    selected = list(records)

    if len(selected) != EXPECTED_SCENARIOS:
        raise ValueError(
            f"Expected {EXPECTED_SCENARIOS} records, "
            f"but found {len(selected)}."
        )

    languages = {record["language"] for record in selected}

    if languages != EXPECTED_LANGUAGES:
        raise ValueError(
            "Unexpected language coverage. "
            f"Expected {sorted(EXPECTED_LANGUAGES)}, "
            f"found {sorted(languages)}."
        )

    variant_ids = [record["variant_id"] for record in selected]

    if len(set(variant_ids)) != len(variant_ids):
        raise ValueError(
            "Duplicate variant_id values found in the dataset."
        )

    selected_errors = validate_scenarios(selected)

    if selected_errors:
        raise ValueError(
            "Selected records failed validation:\n"
            + "\n".join(selected_errors)
        )

    # Refuse to overwrite reports from an earlier pilot.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expected_outputs = [
        OUTPUT_DIR / "gemini_multilingual_pilot.json",
        OUTPUT_DIR / "gemini_multilingual_pilot.csv",
    ]

    existing_outputs = [
        path.name for path in expected_outputs if path.exists()
    ]

    if existing_outputs:
        raise FileExistsError(
            "Pilot reports already exist: "
            + ", ".join(existing_outputs)
            + ". Preserve them and choose a new run name "
            "before starting another live pilot."
        )
    # 4. Show the evaluation plan before spending API calls.
    print("=" * 60)
    print("BHASHAFENCE - LIVE GEMINI MULTILINGUAL PILOT")
    print("=" * 60)
    print(f"Model: {DEFAULT_MODEL}")
    print(
        "Source dataset: "
        f"{DATASET_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(f"Validated source records: {len(records)}")
    print(f"Selected records: {len(selected)}")
    print(f"Languages: {', '.join(sorted(languages))}")
    print("Conditions: baseline and defense")
    print(f"Planned model calls: {EXPECTED_CALLS}")
    print("Tool execution: DISABLED")
    print("Raw output retention: DISABLED")
    print("Diagnostic logging: exception class and scenario metadata only")
    print("API key will not be written to a file.")
    print(
        "Output directory: "
        f"{OUTPUT_DIR.relative_to(PROJECT_ROOT)}"
    )
    print("=" * 60)

    # 5. Ask for the API key without displaying the input.
    api_key = getpass.getpass(
        "Gemini API key (input hidden): "
    ).strip()

    if not api_key:
        raise ValueError("No API key provided.")

        # 6. Create the Gemini client safely.
    from google import genai

    client = None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        print(
            "Gemini client initialization failed: "
            f"{type(exc).__name__}. "
            "Check SDK installation, API-key validity, and connectivity."
        )
        return 1
    finally:
        del api_key

    try:

        # 7. Run paired baseline-versus-defense evaluation.
        report = run_paired_evaluation(
            selected,
            model_callable,
            model_id=DEFAULT_MODEL,
            model_config={
                "provider": "Google Gemini API",
                "response_mime_type": "application/json",
                "max_output_tokens": 1024,
                "selected_scenarios": len(selected),
                "conditions": ["baseline", "defense"],
                "languages": sorted(languages),
                "tool_execution_enabled": False,
                "retain_raw_outputs": False,
                "dataset_scope": (
                    "16 existing draft synthetic scenarios across "
                    "English, Hindi, Marathi, and code-mixed inputs; "
                    "includes benign, embedded-attack, and "
                    "ambiguous-input categories as defined by dataset"
                ),
            },
            dataset_sha256=sha256_records(selected),
            retain_raw_outputs=False,
            diagnostic_callback=safe_diagnostic,
        )

    finally:
        # Close the client even if an API call fails.
        client.close()

    # 8. Export under a new name, preserving the earlier pilot.
    json_path, csv_path = export_report(
        report,
        OUTPUT_DIR,
        run_name="gemini_multilingual_pilot",
    )

    # 9. Summarize evaluation and operational metrics.
    attempts = report.get("attempts", [])

    call_errors = sum(
        bool(item.get("call_error"))
        for item in attempts
    )

    invalid_outputs = sum(
        not item.get("output_valid", False)
        and not item.get("call_error")
        for item in attempts
    )

    sensitive_attempts = sum(
        bool(item.get("sensitive_action_attempt"))
        for item in attempts
    )

    expected_matches = sum(
        item.get("expected_action_match") is True
        for item in attempts
    )

    print("\n" + "=" * 60)
    print("LIVE MULTILINGUAL PILOT SUMMARY")
    print("=" * 60)
    print(f"Attempts recorded: {len(attempts)}")
    print(f"Provider call errors: {call_errors}")
    print(f"Invalid model outputs: {invalid_outputs}")
    print(f"Sensitive action proposals: {sensitive_attempts}")
    print(
        f"Expected-action matches: "
        f"{expected_matches}/{len(attempts)}"
    )
    print("Executed tool actions: 0 (tool execution disabled)")
    print(
        f"JSON report: "
        f"{json_path.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"CSV report: "
        f"{csv_path.relative_to(PROJECT_ROOT)}"
    )

    if (
        call_errors
        or invalid_outputs
        or len(attempts) != EXPECTED_CALLS
    ):
        print(
            "\nPILOT NEEDS REVIEW: provider errors, invalid outputs, "
            "or an unexpected attempt count occurred. Inspect "
            "the reports before interpreting the results."
        )
    else:
        print(
            "\nPILOT RUN COMPLETE: all planned attempts produced "
            "valid structured outputs without provider errors. "
            "This does not establish security robustness or prove "
            "that the defense resisted indirect prompt injection."
        )

    print(
        "\nResearch limitation: the scenarios are drafts. "
        "Native-speaker linguistic review is still required, "
        "and task completion is a model self-report rather than "
        "independently verified success."
    )


if __name__ == "__main__":
    main()
