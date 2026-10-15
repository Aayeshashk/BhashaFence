
import json
from pathlib import Path

from backend.app.policy import PolicyEnforcedExecutor
from backend.app.simulator import ToolCall


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = (
    ROOT / "dataset" / "processed" / "multilingual" / "scenarios.json"
)

EXPECTED_LANGUAGES = {"en", "hi", "mr", "code_mixed"}
EXPECTED_SENSITIVE_TOOLS = {"read_private_note", "send_message"}


def load_scenarios():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_dataset_has_unique_variant_ids():
    scenarios = load_scenarios()
    variant_ids = [item["variant_id"] for item in scenarios]

    assert len(variant_ids) == len(set(variant_ids))


def test_dataset_covers_all_four_languages():
    scenarios = load_scenarios()

    assert {item["language"] for item in scenarios} == EXPECTED_LANGUAGES


def test_each_scenario_has_four_language_variants():
    scenarios = load_scenarios()
    scenario_ids = {item["scenario_id"] for item in scenarios}

    assert len(scenarios) == 24

    for scenario_id in scenario_ids:
        variants = [
            item for item in scenarios
            if item["scenario_id"] == scenario_id
        ]
        assert len(variants) == 4
        assert {item["language"] for item in variants} == EXPECTED_LANGUAGES


def test_matched_variants_preserve_structured_action():
    scenarios = load_scenarios()
    scenario_ids = {item["scenario_id"] for item in scenarios}

    for scenario_id in scenario_ids:
        variants = [
            item for item in scenarios
            if item["scenario_id"] == scenario_id
        ]
        reference = variants[0]

        for variant in variants[1:]:
            assert variant["tool_name"] == reference["tool_name"]
            assert variant["arguments"] == reference["arguments"]
            assert variant["source"] == reference["source"]
            assert variant["legitimate_task"] == reference["legitimate_task"]
            assert (
                variant["expected_defense_status"]
                == reference["expected_defense_status"]
            )


def test_hindi_and_marathi_text_loads_as_unicode():
    scenarios = load_scenarios()

    for language in ("hi", "mr"):
        texts = [
            item["text"] for item in scenarios
            if item["language"] == language
        ]
        assert len(texts) == 6
        assert all(text.strip() for text in texts)
        assert any(any(ord(char) > 127 for char in text) for text in texts)


def test_defense_matches_expected_status_for_all_variants():
    scenarios = load_scenarios()
    executor = PolicyEnforcedExecutor()

    for scenario in scenarios:
        result = executor.execute(
            ToolCall(
                tool_name=scenario["tool_name"],
                arguments=dict(scenario["arguments"]),
                source=scenario["source"],
            )
        )

        assert result.status == scenario["expected_defense_status"], (
            scenario["variant_id"],
            result.status,
            result.reason,
        )


def test_untrusted_sensitive_actions_never_execute():
    scenarios = load_scenarios()
    executor = PolicyEnforcedExecutor()

    for scenario in scenarios:
        executor.execute(
            ToolCall(
                tool_name=scenario["tool_name"],
                arguments=dict(scenario["arguments"]),
                source=scenario["source"],
            )
        )

    executed_sensitive_actions = [
        action for action in executor.world.executed_actions
        if action["tool_name"] in EXPECTED_SENSITIVE_TOOLS
        and action["source"] == "untrusted_content"
    ]

    assert executed_sensitive_actions == []
