
import json
from copy import deepcopy
from pathlib import Path

from scripts.audit_indirect_injection_pilot import audit_dataset


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


def test_current_pilot_passes_structural_audit():
    report = audit_dataset(load_dataset())

    assert report["passed"] is True
    assert report["record_count"] == 16
    assert report["errors"] == []


def test_missing_variant_is_detected():
    records = load_dataset()
    records.pop()

    report = audit_dataset(records)

    assert report["passed"] is False
    assert any("Expected 16 records" in error for error in report["errors"])


def test_matched_variant_action_mismatch_is_detected():
    records = deepcopy(load_dataset())
    records[1]["expected_action"] = {"type": "no_action"}

    report = audit_dataset(records)

    assert report["passed"] is False
    assert any(
        "variants disagree on expected_action" in error
        for error in report["errors"]
    )


def test_non_draft_record_is_detected():
    records = deepcopy(load_dataset())
    records[0]["review_status"] = "approved"

    report = audit_dataset(records)

    assert report["passed"] is False
    assert any(
        "must remain draft" in error
        for error in report["errors"]
    )


def test_wrong_source_metadata_is_detected():
    records = deepcopy(load_dataset())
    records[0]["source_metadata"] = "user"

    report = audit_dataset(records)

    assert report["passed"] is False
    assert any(
        "source metadata must identify the untrusted content"
        in error
        for error in report["errors"]
    )


def test_audit_does_not_modify_input_records():
    records = load_dataset()
    original = deepcopy(records)

    audit_dataset(records)

    assert records == original
