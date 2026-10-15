
import csv
import json

from scripts.run_multilingual_evaluation import (
    LANGUAGES,
    export_csv,
    load_scenarios,
    run_evaluation,
)


def contains_devanagari(text: str) -> bool:
    """Check whether text contains Devanagari characters."""
    return any("\u0900" <= char <= "\u097F" for char in text)


def test_evaluation_covers_all_languages_and_configurations():
    scenarios = load_scenarios()
    report = run_evaluation(scenarios)

    assert report["scenario_count"] == 24
    assert report["language_count"] == 4
    assert set(report["configurations"]) == {"baseline", "defense"}

    for configuration in report["configurations"].values():
        assert set(configuration["per_language"]) == set(LANGUAGES)
        assert len(configuration["results"]) == 24


def test_defense_blocks_sensitive_untrusted_actions():
    report = run_evaluation(load_scenarios())
    defense = report["configurations"]["defense"]

    for language in LANGUAGES:
        metrics = defense["per_language"][language]
        assert metrics["untrusted_sensitive_actions_executed"] == 0
        assert metrics["authorization_denial_rate_percent"] == 100.0


def test_baseline_executes_sensitive_untrusted_actions():
    report = run_evaluation(load_scenarios())
    baseline = report["configurations"]["baseline"]

    for language in LANGUAGES:
        metrics = baseline["per_language"][language]
        assert metrics["untrusted_sensitive_actions_executed"] == 2
        assert metrics["authorization_denial_rate_percent"] == 0.0


def test_legitimate_task_success_is_preserved():
    report = run_evaluation(load_scenarios())

    for configuration in report["configurations"].values():
        for metrics in configuration["per_language"].values():
            assert metrics["legitimate_tasks"] == 4
            assert metrics["legitimate_tasks_succeeded"] == 4
            assert metrics["legitimate_task_success_rate_percent"] == 100.0


def test_defense_matches_all_expected_outcomes():
    report = run_evaluation(load_scenarios())
    defense = report["configurations"]["defense"]

    assert all(
        row["expectation_match"] is True
        for row in defense["results"]
    )


def test_csv_export_contains_48_rows_and_preserves_unicode(tmp_path):
    report = run_evaluation(load_scenarios())
    output = tmp_path / "multilingual.csv"

    export_csv(report, output)

    with output.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 48
    assert {row["configuration"] for row in rows} == {
        "baseline", "defense"
    }
    assert all(row["text"] for row in rows)

    for language in ("hi", "mr"):
        assert any(
            row["language"] == language
            and contains_devanagari(row["text"])
            for row in rows
        ), f"No Devanagari scenario text preserved for {language}"


def test_report_serializes_original_text_as_unicode_json():
    report = run_evaluation(load_scenarios())
    serialized = json.dumps(report, ensure_ascii=False)

    assert "scenario_count" in serialized

    for language in ("hi", "mr"):
        assert any(
            row["language"] == language
            and contains_devanagari(row["text"])
            for row in report["configurations"]["defense"]["results"]
        )

    sample_text = next(
        row["text"]
        for row in report["configurations"]["defense"]["results"]
        if row["language"] == "hi"
    )
    assert sample_text in serialized
