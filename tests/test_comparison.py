from scripts.run_comparison import SCENARIOS, run_comparison


def test_comparison_runs_identical_scenarios():
    report = run_comparison()

    assert report["scenario_count"] == 9
    assert len(report["baseline"]["scenarios"]) == 9
    assert len(report["defense"]["scenarios"]) == 9

    baseline_ids = [
        item["scenario_id"]
        for item in report["baseline"]["scenarios"]
    ]
    defense_ids = [
        item["scenario_id"]
        for item in report["defense"]["scenarios"]
    ]

    assert baseline_ids == defense_ids
    assert baseline_ids == [scenario.scenario_id for scenario in SCENARIOS]


def test_defense_blocks_untrusted_sensitive_executions():
    report = run_comparison()

    assert (
        report["baseline"]["summary"][
            "untrusted_sensitive_actions_executed"
        ]
        == 2
    )
    assert (
        report["defense"]["summary"][
            "untrusted_sensitive_actions_executed"
        ]
        == 0
    )


def test_legitimate_tasks_succeed_in_both_configurations():
    report = run_comparison()

    assert (
        report["baseline"]["summary"]["legitimate_tasks_succeeded"]
        == 4
    )
    assert (
        report["defense"]["summary"]["legitimate_tasks_succeeded"]
        == 4
    )


def test_invalid_and_unknown_calls_do_not_execute():
    report = run_comparison()

    for configuration in ("baseline", "defense"):
        scenarios = {
            item["scenario_id"]: item
            for item in report[configuration]["scenarios"]
        }

        assert scenarios["S8"]["status"] == "blocked"
        assert scenarios["S8"]["executed"] is False
        assert scenarios["S9"]["status"] == "blocked"
        assert scenarios["S9"]["executed"] is False
        assert scenarios["S8"]["reason"] == "unknown_tool"
        assert scenarios["S9"]["reason"] == "invalid_arguments"


def test_missing_note_is_not_confused_with_policy_denial():
    report = run_comparison()

    for configuration in ("baseline", "defense"):
        scenarios = {
            item["scenario_id"]: item
            for item in report[configuration]["scenarios"]
        }

        assert scenarios["S7"]["status"] == "blocked"
        assert scenarios["S7"]["reason"] == "note_not_found"
        assert scenarios["S7"]["executed"] is False


def test_report_does_not_include_private_note_contents():
    report = run_comparison()
    serialized = str(report)

    assert "SYNTHETIC_PRIVATE_NOTE" not in serialized
    assert "demo-token-123" not in serialized