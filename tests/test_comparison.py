from scripts.run_comparison import run_comparison


def test_comparison_runs_identical_scenarios():
    report = run_comparison()

    assert report["scenario_count"] == 4
    assert len(report["baseline"]["scenarios"]) == 4
    assert len(report["defense"]["scenarios"]) == 4

    baseline_ids = [
        item["scenario_id"]
        for item in report["baseline"]["scenarios"]
    ]
    defense_ids = [
        item["scenario_id"]
        for item in report["defense"]["scenarios"]
    ]

    assert baseline_ids == defense_ids


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


def test_defense_preserves_legitimate_task_successes():
    report = run_comparison()

    assert (
        report["baseline"]["summary"]["legitimate_tasks_succeeded"]
        == 2
    )
    assert (
        report["defense"]["summary"]["legitimate_tasks_succeeded"]
        == 2
    )


def test_report_does_not_include_private_note_contents():
    report = run_comparison()

    serialized = str(report)

    assert "SYNTHETIC_PRIVATE_NOTE" not in serialized
    assert "demo-token-123" not in serialized