
"""Run a targeted, non-executing Gemini diagnostic on S3-en."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google import genai

from backend.app.gemini_adapter import (
    DEFAULT_MODEL,
    GeminiAdapterError,
    create_gemini_callable,
)
from backend.app.model_evaluation import build_messages


def main():
    records_path = Path(
        "dataset/processed/indirect_injection/pilot_scenarios.json"
    )
    client = None

    try:
        # Load and validate the target scenario.
        records = json.loads(
            records_path.read_text(encoding="utf-8")
        )

        if not isinstance(records, list):
            print("Diagnostic aborted: dataset must be a JSON list.")
            return

        matches = [
            item
            for item in records
            if isinstance(item, dict)
            and item.get("variant_id") == "S3-en"
        ]

        if len(matches) != 1:
            print(
                "Diagnostic aborted: expected exactly one "
                "S3-en scenario."
            )
            return

        record = matches[0]

        print("Scenario:", record["variant_id"])
        print("Conditions: baseline and defense")
        print("Model:", DEFAULT_MODEL)
        print("Tool execution: DISABLED")
        print("Raw output retention: DISABLED")

        # Reuse one client for both conditions.
        client = genai.Client()
        call_model = create_gemini_callable(client=client)

        for condition in ("baseline", "defense"):
            print(f"\nTesting condition: {condition}")

            try:
                messages = build_messages(record, condition)
                output = call_model(messages)

                print("Request status: SUCCESS")
                print("Output received:", bool(output))
                print("Output length:", len(output))

            except GeminiAdapterError as exc:
                print("Request status: FAILED")
                print(
                    "Provider exception type:",
                    exc.provider_exception_type,
                )
                print("Diagnostic code:", exc.diagnostic_code)
                print("Sanitized error:", str(exc))

            except Exception as exc:
                print("Request status: FAILED")
                print("Provider exception type:", type(exc).__name__)
                print("Diagnostic code: UNCLASSIFIED")
                print("Error details withheld.")

        print("\nDiagnostic finished. No tools were executed.")
        print("No model output was saved.")

    except Exception as exc:
        print("\nDiagnostic setup failed.")
        print("Exception type:", type(exc).__name__)
        print("Error details withheld.")

    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                print("Client cleanup failed; details withheld.")


if __name__ == "__main__":
    main()
