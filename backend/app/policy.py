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
    """Simulator protected by a simple source-aware policy."""

    def execute(self, call: ToolCall) -> ToolResult:
        if (
            call.tool_name not in SENSITIVE_TOOLS
            or call.source not in UNTRUSTED_SOURCES
        ):
            return super().execute(call)

        # Let the simulator classify malformed arguments accurately.
        # Do not inspect private resource existence before authorization.
        if not isinstance(call.arguments, dict):
            return super().execute(call)

        args = call.arguments

        if call.tool_name == "read_private_note":
            if not isinstance(args.get("note_id"), str):
                return super().execute(call)

        if call.tool_name == "send_message":
            if (
                not isinstance(args.get("recipient"), str)
                or not isinstance(args.get("message"), str)
            ):
                return super().execute(call)

        # Valid, sensitive requests from untrusted content are denied
        # before the underlying tool can access a resource or act.
        return self._finish(
            call,
            "blocked",
            None,
            "policy_denied_untrusted_sensitive_action",
        )