
"""Evaluate matched multilingual scenarios against baseline and defense.

All tool effects are synthetic. Natural-language interpretation is not
performed by this runner: the dataset supplies the structured tool call.
"""

import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.policy import PolicyEnforcedExecutor
from backend.app.simulator import ToolCall, ToolExecutor


DATASET_PATH = (
    ROOT / "dataset" / "processed" / "multilingual" / "scenarios.json"
)
OUTPUT_DIR = ROOT / "artifacts"
LANGUAGES = ("en", "hi", "mr", "code_mixed")
SENSITIVE_TOOLS = {"read_private_note", "send_message"}
POLICY_DENIAL = "policy_denied_untrusted_sensitive_action"


def load_scenarios() -> list[dict[str, Any]]:
    """Load and minimally validate the multilingual dataset."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        scenarios = json.load(file)

    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Dataset must be a non-empty JSON list.")

    required_fields = {
        "variant_id",
        "scenario_id",
        "language",
        "text",
        "source",
        "tool_name",
        "arguments",
        "legitimate_task",
        "expected_defense_status",
    }

    variant_ids = set()

    for scenario in scenarios:
        missing = required_fields - scenario.keys()
        if missing:
            raise ValueError(
                f"Scenario is missing fields {sorted(missing)}: "
                f"{scenario.get('variant_id', '<unknown>')}"
            )

        if scenario["language"] not in LANGUAGES:
            raise ValueError(
                f"Unsupported language: {scenario['language']}"
            )

        if scenario["variant_id"] in variant_ids:
            raise ValueError(
                f"Duplicate variant ID: {scenario['variant_id']}"
            )

        variant_ids.add(scenario["variant_id"])

    return scenarios


def is_well_formed_sensitive(scenario: dict[str, Any]) -> bool:
    """Match the simulator's argument-type requirements for sensitive tools."""
    args = scenario["arguments"]

    if scenario["tool_name"] == "read_private_note":
        return isinstance(args.get("note_id"), str)

    if scenario["tool_name"] == "send_message":
        return (
            isinstance(args.get("recipient"), str)
            and isinstance(args.get("message"), str)
        )

    return False


def run_evaluation(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run each language separately with fresh synthetic worlds."""
    configurations = {
        "baseline": ToolExecutor,
        "defense": PolicyEnforcedExecutor,
    }

    report: dict[str, Any] = {
        "experiment": (
            "BhashaFence multilingual synthetic authorization evaluation"
        ),
        "dataset_path": str(DATASET_PATH.relative_to(ROOT)),
        "scenario_count": len(scenarios),
        "language_count": len({s["language"] for s in scenarios}),
        "limitations": [
            "All tool effects are synthetic.",
            "The harness supplies structured tool calls; natural-language "
            "interpretation is not evaluated.",
            "Source labels are supplied by the dataset.",
            "Translations require independent semantic review.",
            "Results are a functional pilot, not statistical evidence.",
        ],
        "configurations": {},
    }

    for configuration_name, executor_class in configurations.items():
        rows = []

        for language in LANGUAGES:
            language_scenarios = [
                scenario
                for scenario in scenarios
                if scenario["language"] == language
            ]
            executor = executor_class()

            for scenario in language_scenarios:
                actions_before = len(executor.world.executed_actions)

                result = executor.execute(
                    ToolCall(
                        tool_name=scenario["tool_name"],
                        arguments=dict(scenario["arguments"]),
                        source=scenario["source"],
                    )
                )

                executed = (
                    len(executor.world.executed_actions) > actions_before
                )

                rows.append({
                    "configuration": configuration_name,
                    "language": language,
                    "variant_id": scenario["variant_id"],
                    "scenario_id": scenario["scenario_id"],
                    "text": scenario["text"],
                    "source": scenario["source"],
                    "legitimate_task": scenario["legitimate_task"],
                    "tool_name": scenario["tool_name"],
                    "sensitive_tool": (
                        scenario["tool_name"] in SENSITIVE_TOOLS
                    ),
                    "status": result.status,
                    "reason": result.reason,
                    "executed": executed,
                    "expected_defense_status": (
                        scenario["expected_defense_status"]
                    ),
                    "expectation_match": (
                        result.status == scenario["expected_defense_status"]
                        if configuration_name == "defense"
                        else None
                    ),
                })

        per_language = {}

        for language in LANGUAGES:
            language_rows = [
                row for row in rows if row["language"] == language
            ]

            legitimate = [
                row for row in language_rows if row["legitimate_task"]
            ]

            eligible = [
                row for row in language_rows
                if row["source"] == "untrusted_content"
                and row["sensitive_tool"]
                and is_well_formed_sensitive(
                    next(
                        scenario for scenario in scenarios
                        if scenario["variant_id"] == row["variant_id"]
                    )
                )
            ]

            denials = sum(
                row["reason"] == POLICY_DENIAL for row in eligible
            )

            legitimate_successes = sum(
                row["status"] == "success" for row in legitimate
            )

            per_language[language] = {
                "scenario_count": len(language_rows),
                "legitimate_tasks": len(legitimate),
                "legitimate_tasks_succeeded": legitimate_successes,
                "legitimate_task_success_rate_percent": round(
                    100 * legitimate_successes / len(legitimate), 2
                ) if legitimate else 0.0,
                "eligible_untrusted_sensitive_requests": len(eligible),
                "explicit_authorization_denials": denials,
                "authorization_denial_rate_percent": round(
                    100 * denials / len(eligible), 2
                ) if eligible else 0.0,
                "untrusted_sensitive_actions_executed": sum(
                    row["executed"] for row in eligible
                ),
                "defense_expectations_matched": (
                    sum(
                        row["expectation_match"] is True
                        for row in language_rows
                    )
                    if configuration_name == "defense"
                    else None
                ),
            }

        report["configurations"][configuration_name] = {
            "per_language": per_language,
            "results": rows,
        }

    return report


def export_csv(report: dict[str, Any], path: Path) -> None:
    """Write per-variant outcomes and original text as UTF-8 CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "configuration",
        "language",
        "variant_id",
        "scenario_id",
        "text",
        "source",
        "legitimate_task",
        "tool_name",
        "sensitive_tool",
        "status",
        "reason",
        "executed",
        "expected_defense_status",
        "expectation_match",
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for configuration in ("baseline", "defense"):
            for row in report["configurations"][configuration]["results"]:
                writer.writerow({
                    field: row[field] for field in fields
                })


def main() -> None:
    scenarios = load_scenarios()
    report = run_evaluation(scenarios)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "multilingual_evaluation.json"
    csv_path = OUTPUT_DIR / "multilingual_evaluation.csv"

    export_csv(report, csv_path)

    report["exports"] = {
        "json": str(json_path.relative_to(ROOT)),
        "csv": str(csv_path.relative_to(ROOT)),
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
