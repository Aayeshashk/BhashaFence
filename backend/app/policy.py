"""Deterministic authorization policy for BhashaFence."""

from backend.app.simulator import ToolCall, ToolExecutor, ToolResult


SENSITIVE_TOOLS = frozenset({
    "read_private_note",
    "send_message",
})

UNTRUSTED_SOURCES = frozenset({
    "untrusted_content",
})


class PolicyEnforcedExecutor(ToolExecutor):
    """Simulator protected by a simple source-aware policy.

    This initial defense blocks sensitive tool calls originating
    from explicitly labelled untrusted content. It is a research
    baseline, not a complete prompt-injection defense.
    """

    def execute(self, call: ToolCall) -> ToolResult:
        if (
            call.tool_name in SENSITIVE_TOOLS
            and call.source in UNTRUSTED_SOURCES
        ):
            return self._finish(
                call,
                "blocked",
                None,
                "policy_denied_untrusted_sensitive_action",
            )

        return super().execute(call)