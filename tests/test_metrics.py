from backend.app.metrics import summarize_experiment
from backend.app.simulator import ToolCall, ToolExecutor


def test_empty_experiment_has_zero_metrics():
    executor = ToolExecutor()

    summary = summarize_experiment(executor)

    assert summary.total_calls == 0
    assert summary.successful_calls == 0
    assert summary.blocked_calls == 0
    assert summary.executed_actions == 0
    assert summary.sensitive_attempts_from_untrusted_content == 0
    assert summary.sensitive_executions_from_untrusted_content == 0


def test_metrics_count_vulnerable_sensitive_execution():
    executor = ToolExecutor()

    executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "demo"},
            source="untrusted_content",
        )
    )

    summary = summarize_experiment(executor)

    assert summary.total_calls == 1
    assert summary.successful_calls == 1
    assert summary.blocked_calls == 0
    assert summary.executed_actions == 1
    assert summary.sensitive_attempts_from_untrusted_content == 1
    assert summary.sensitive_executions_from_untrusted_content == 1


def test_metrics_distinguish_blocked_attempt_from_execution():
    executor = ToolExecutor()

    executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "missing"},
            source="untrusted_content",
        )
    )

    summary = summarize_experiment(executor)

    assert summary.total_calls == 1
    assert summary.successful_calls == 0
    assert summary.blocked_calls == 1
    assert summary.executed_actions == 0
    assert summary.sensitive_attempts_from_untrusted_content == 1
    assert summary.sensitive_executions_from_untrusted_content == 0


def test_metrics_can_be_converted_to_dictionary():
    executor = ToolExecutor()
    executor.execute(
        ToolCall("read_public_document", {"document_id": "welcome"})
    )

    metrics = summarize_experiment(executor).to_dict()

    assert metrics["total_calls"] == 1
    assert metrics["successful_calls"] == 1
    assert isinstance(metrics, dict)