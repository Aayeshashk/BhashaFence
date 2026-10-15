from backend.app.policy import PolicyEnforcedExecutor
from backend.app.simulator import ToolCall


def test_untrusted_private_note_access_is_blocked():
    executor = PolicyEnforcedExecutor()

    result = executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "demo"},
            source="untrusted_content",
        )
    )

    assert result.status == "blocked"
    assert result.reason == (
        "policy_denied_untrusted_sensitive_action"
    )
    assert executor.world.executed_actions == []
    assert len(executor.audit_log) == 1


def test_untrusted_message_sending_is_blocked():
    executor = PolicyEnforcedExecutor()

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

    assert result.status == "blocked"
    assert executor.world.outbox == []
    assert executor.world.executed_actions == []
    assert executor.audit_log[0].reason == (
        "policy_denied_untrusted_sensitive_action"
    )


def test_user_can_read_private_note_in_simulator():
    executor = PolicyEnforcedExecutor()

    result = executor.execute(
        ToolCall(
            "read_private_note",
            {"note_id": "demo"},
            source="user",
        )
    )

    assert result.status == "success"
    assert "SYNTHETIC_PRIVATE_NOTE" in result.output
    assert len(executor.world.executed_actions) == 1


def test_untrusted_public_document_read_remains_allowed():
    executor = PolicyEnforcedExecutor()

    result = executor.execute(
        ToolCall(
            "read_public_document",
            {"document_id": "welcome"},
            source="untrusted_content",
        )
    )

    assert result.status == "success"
    assert "Welcome" in result.output
    assert len(executor.world.executed_actions) == 1