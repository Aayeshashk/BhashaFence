
from backend.app.simulator import ToolCall, ToolExecutor


def test_reads_public_document():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "read_public_document",
            {"document_id": "welcome"},
        )
    )

    assert result.status == "success"
    assert "Welcome" in result.output
    assert len(executor.audit_log) == 1


def test_baseline_allows_sensitive_action_from_untrusted_content():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "demo"},
            source="untrusted_content",
        )
    )

    # Expected behavior of the deliberately vulnerable baseline.
    assert result.status == "success"
    assert "SYNTHETIC_PRIVATE_NOTE" in result.output


def test_message_tool_only_uses_synthetic_outbox():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "send_message",
            {
                "recipient": "demo@example.test",
                "message": "Synthetic test message",
            },
            source="untrusted_content",
        )
    )

    assert result.status == "success"
    assert len(executor.world.outbox) == 1
    assert executor.world.outbox[0]["recipient"] == (
        "demo@example.test"
    )


def test_unknown_tool_is_blocked():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall("delete_everything", {})
    )

    assert result.status == "blocked"
    assert result.reason == "unknown_tool"
    assert executor.world.executed_actions == []


def test_invalid_arguments_are_blocked():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "send_message",
            {"recipient": 123, "message": "test"},
        )
    )

    assert result.status == "blocked"
    assert result.reason == "invalid_arguments"
    assert executor.world.outbox == []
def test_blocked_tool_call_is_recorded_in_audit_log():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "unknown_tool",
            {},
            source="untrusted_content",
        )
    )

    assert result.status == "blocked"
    assert len(executor.audit_log) == 1

    event = executor.audit_log[0]
    assert event.tool_name == "unknown_tool"
    assert event.source == "untrusted_content"
    assert event.status == "blocked"
    assert event.reason == "unknown_tool"


def test_missing_private_note_does_not_change_world():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "missing"},
            source="untrusted_content",
        )
    )

    assert result.status == "blocked"
    assert result.reason == "note_not_found"
    assert executor.world.executed_actions == []
    assert len(executor.audit_log) == 1
    assert executor.audit_log[0].status == "blocked"


def test_audit_log_preserves_successful_call_source():
    executor = ToolExecutor()

    result = executor.execute(
        ToolCall(
            "read_public_document",
            {"document_id": "welcome"},
            source="user",
        )
    )

    assert result.status == "success"
    assert len(executor.audit_log) == 1

    event = executor.audit_log[0]
    assert event.tool_name == "read_public_document"
    assert event.source == "user"
    assert event.status == "success"
    assert event.reason == "public_document_read"
