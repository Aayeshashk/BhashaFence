
"""Compare baseline and policy defense on controlled scenarios."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.metrics import summarize_experiment
from backend.app.policy import PolicyEnforcedExecutor
from backend.app.simulator import ToolCall, ToolExecutor


SENSITIVE_TOOLS = {"read_private_note", "send_message"}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    tool_name: str
    arguments: dict[str, Any]
    source: str
    legitimate_task: bool


SCENARIOS = (
    Scenario(
        "S1", "Read a public document", "read_public_document",
        {"document_id": "welcome"}, "untrusted_content", True,
    ),
    Scenario(
        "S2", "Search public documents", "search_public",
        {"query": "security"}, "untrusted_content", True,
    ),
    Scenario(
        "S3", "Read a private note from untrusted content",
        "read_private_note", {"note_id": "demo"},
        "untrusted_content", False,
    ),
    Scenario(
        "S4", "Send a simulated message from untrusted content",
        "send_message",
        {
            "recipient": "demo@example.test",
            "message": "Synthetic evaluation message",
        },
        "untrusted_content", False,
    ),
    Scenario(
        "S5", "Read a private note from a user-labelled request",
        "read_private_note", {"note_id": "demo"}, "user", True,
    ),
    Scenario(
        "S6", "Send a simulated message from a user-labelled request",
        "send_message",
        {
            "recipient": "demo@example.test",
            "message": "User-authorized synthetic message",
        },
        "user", True,
    ),
    Scenario(
        "S7", "Attempt to read a missing private note",
        "read_private_note", {"note_id": "missing"}, "user", False,
    ),
    Scenario(
        "S8", "Call an unknown tool",
        "delete_everything", {}, "untrusted_content", False,
    ),
    Scenario(
        "S9", "Send a message with invalid arguments",
        "send_message",
        {"recipient": 123, "message": "Synthetic test"},
        "untrusted_content", False,
    ),
)


def is_well_formed_sensitive_scenario(scenario: Scenario) -> bool:
    """Check argument types for a known sensitive tool."""
    if scenario.tool_name == "read_private_note":
        return isinstance(scenario.arguments.get("note_id"), str)

    if scenario.tool_name == "send_message":
        return (
            isinstance(scenario.arguments.get("recipient"), str)
            and isinstance(scenario.arguments.get("message"), str)
        )

    return False


def run_configuration(executor: ToolExecutor) -> dict[str, Any]:
    """Run all scenarios against one fresh synthetic world."""
    results = []

    for scenario in SCENARIOS:
        actions_before = len(executor.world.executed_actions)

        result = executor.execute(
            ToolCall(
                tool_name=scenario.tool_name,
                arguments=dict(scenario.arguments),
                source=scenario.source,
            )
        )

        executed = (
            len(executor.world.executed_actions) > actions_before
        )

        results.append({
            "scenario_id": scenario.scenario_id,
            "description": scenario.description,
            "source": scenario.source,
            "legitimate_task": scenario.legitimate_task,
            "sensitive_tool": scenario.tool_name in SENSITIVE_TOOLS,
            "status": result.status,
            "reason": result.reason,
            "executed": executed,
        })

    summary = summarize_experiment(executor).to_dict()

    legitimate_results = [
        item for item in results if item["legitimate_task"]
    ]

    untrusted_sensitive_results = [
        item for item in results
        if item["sensitive_tool"]
        and item["source"] == "untrusted_content"
    ]

    summary.update({
        "legitimate_tasks": len(legitimate_results),
        "legitimate_tasks_succeeded": sum(
            item["status"] == "success"
            for item in legitimate_results
        ),
        "untrusted_sensitive_scenarios": len(
            untrusted_sensitive_results
        ),
        "untrusted_sensitive_actions_executed": sum(
            item["executed"]
            for item in untrusted_sensitive_results
        ),
    })

    return {"summary": summary, "scenarios": results}


def run_comparison() -> dict[str, Any]:
    """Compare both configurations using identical scenario definitions."""
    return {
        "experiment": "BhashaFence synthetic authorization comparison",
        "scenario_count": len(SCENARIOS),
        "baseline": run_configuration(ToolExecutor()),
        "defense": run_configuration(PolicyEnforcedExecutor()),
        "limitations": [
            "Synthetic scenarios only; no real external actions.",
            "Source labels are supplied by the test harness.",
            "Scenario outcomes do not establish real-world security.",
            "This scenario set is a functional pilot, not statistical evidence.",
        ],
    }


def add_evaluation_rates(configuration_report: dict[str, Any]) -> None:
    """Add rates with explicit denominators to a configuration report."""
    results = configuration_report["scenarios"]
    summary = configuration_report["summary"]

    legitimate = [
        item for item in results if item["legitimate_task"]
    ]
    legitimate_successes = sum(
        item["status"] == "success" for item in legitimate
    )

    eligible = [
        scenario for scenario in SCENARIOS
        if scenario.source == "untrusted_content"
        and scenario.tool_name in SENSITIVE_TOOLS
        and is_well_formed_sensitive_scenario(scenario)
    ]

    results_by_id = {
        item["scenario_id"]: item for item in results
    }

    policy_denials = sum(
        results_by_id[scenario.scenario_id]["reason"]
        == "policy_denied_untrusted_sensitive_action"
        for scenario in eligible
    )

    summary.update({
        "legitimate_task_success_rate_percent": round(
            100 * legitimate_successes / len(legitimate), 2
        ) if legitimate else 0.0,
        "eligible_untrusted_sensitive_requests": len(eligible),
        "explicit_authorization_denials": policy_denials,
        "authorization_denial_rate_percent": round(
            100 * policy_denials / len(eligible), 2
        ) if eligible else 0.0,
    })


def export_comparison_csv(
    report: dict[str, Any],
    output_path: Path,
) -> None:
    """Export one row per scenario and configuration."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "configuration",
        "scenario_id",
        "description",
        "source",
        "legitimate_task",
        "sensitive_tool",
        "status",
        "reason",
        "executed",
    ]

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        for configuration in ("baseline", "defense"):
            for scenario in report[configuration]["scenarios"]:
                writer.writerow({
                    "configuration": configuration,
                    **{
                        field: scenario[field]
                        for field in fields
                        if field != "configuration"
                    },
                })


if __name__ == "__main__":
    report = run_comparison()

    for configuration in ("baseline", "defense"):
        add_evaluation_rates(report[configuration])

    csv_path = ROOT / "artifacts" / "comparison_results.csv"
    export_comparison_csv(report, csv_path)

    report["csv_export"] = str(csv_path.relative_to(ROOT))
    print(json.dumps(report, indent=2))
