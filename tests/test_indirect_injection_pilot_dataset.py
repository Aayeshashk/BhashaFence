import json
from pathlib import Path

from backend.app.indirect_scenarios import (
    build_model_input,
    validate_scenarios,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = (
    ROOT
    / "dataset"
    / "processed"
    / "indirect_injection"
    / "pilot_scenarios.json"
)


def load_dataset():
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_pilot_dataset_passes_schema_validation():
    assert validate_scenarios(load_dataset()) == []


def test_pilot_has_16_unique_records_and_four_languages():
    records = load_dataset()

    assert len(records) == 16
    assert len({r["variant_id"] for r in records}) == 16
    assert {r["language"] for r in records} == {
        "en", "hi", "mr", "code_mixed"
    }


def test_each_scenario_has_four_matched_variants():
    records = load_dataset()

    for scenario_id in {"S1", "S2", "S3", "S4"}:
        variants = [
            r for r in records if r["scenario_id"] == scenario_id
        ]
        assert len(variants) == 4
        assert {r["language"] for r in variants} == {
            "en", "hi", "mr", "code_mixed"
        }


def test_all_variants_remain_drafts():
    assert all(
        r["review_status"] == "draft"
        for r in load_dataset()
    )


def test_model_input_excludes_evaluator_labels():
    for record in load_dataset():
        model_input = build_model_input(record)

        assert set(model_input) == {
            "user_task",
            "untrusted_content",
        }
        assert "expected_action" not in model_input
        assert "embedded_attack" not in model_input
        assert "source_metadata" not in model_input


def test_existing_multilingual_dataset_is_still_24_records():
    path = ROOT / "dataset" / "processed" / "multilingual" / "scenarios.json"
    existing = json.loads(path.read_text(encoding="utf-8"))

    assert len(existing) == 24