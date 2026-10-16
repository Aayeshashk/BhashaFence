
"""Safe Gemini adapter for provider-neutral model evaluation."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from google import genai
from google.genai import types

from backend.app.indirect_scenarios import build_model_input
from backend.app.model_evaluation import build_messages


DEFAULT_MODEL = "gemini-3.1-flash-lite"

ALLOWED_DIAGNOSTIC_CODES = frozenset(
    {
        "TIMEOUT",
        "RATE_LIMIT_OR_QUOTA",
        "PROVIDER_SERVER_ERROR",
        "AUTHENTICATION_OR_PERMISSION",
        "INVALID_REQUEST",
        "NETWORK_ERROR",
        "OTHER_PROVIDER_ERROR",
        "INVALID_RESPONSE",
    }
)

_PROVIDER_EXCEPTION_TYPE_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]{0,63}\Z"
)


class GeminiAdapterError(RuntimeError):
    """Safe, sanitized error raised by the Gemini adapter."""

    def __init__(
        self,
        message: str,
        *,
        diagnostic_code: str = "OTHER_PROVIDER_ERROR",
        provider_exception_type: str = "Exception",
    ) -> None:
        if (
            not isinstance(diagnostic_code, str)
            or diagnostic_code not in ALLOWED_DIAGNOSTIC_CODES
        ):
            diagnostic_code = "OTHER_PROVIDER_ERROR"

        if (
            not isinstance(provider_exception_type, str)
            or not _PROVIDER_EXCEPTION_TYPE_PATTERN.fullmatch(
                provider_exception_type
            )
        ):
            provider_exception_type = "Exception"

        super().__init__(message)
        self.diagnostic_code = diagnostic_code
        self.provider_exception_type = provider_exception_type


def _classify_provider_exception(exc: Exception) -> str:
    """Classify provider failures without exposing exception contents."""
    exception_type = type(exc).__name__.lower()
    message = str(exc).lower()

    # Recognize standalone HTTP status codes, not substrings in identifiers.
    status_codes = {
        int(code)
        for code in re.findall(
            r"(?<!\d)(400|401|403|408|429|500|502|503|504)(?!\d)",
            message,
        )
    }

    if "timeout" in exception_type or "timed out" in message:
        return "TIMEOUT"

    if (
        "ratelimit" in exception_type
        or "resource_exhausted" in exception_type
        or "too many requests" in message
        or "quota" in message
        or 429 in status_codes
    ):
        return "RATE_LIMIT_OR_QUOTA"

    if (
        "serviceunavailable" in exception_type
        or "internalservererror" in exception_type
        or "server error" in message
        or bool(status_codes.intersection({500, 502, 503, 504}))
    ):
        return "PROVIDER_SERVER_ERROR"

    if (
        "permissiondenied" in exception_type
        or "unauthorized" in exception_type
        or "authentication" in exception_type
        or "api key" in message
        or bool(status_codes.intersection({401, 403}))
    ):
        return "AUTHENTICATION_OR_PERMISSION"

    if (
        "invalidargument" in exception_type
        or "badrequest" in exception_type
        or 400 in status_codes
    ):
        return "INVALID_REQUEST"

    if "connection" in exception_type or "network" in exception_type:
        return "NETWORK_ERROR"

    return "OTHER_PROVIDER_ERROR"


def _validate_model_name(model: str) -> str:
    """Require a non-empty model name."""
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string")

    return model.strip()


def _create_client(
    api_key: str | None,
    client_factory: Callable[..., Any] | None,
) -> Any:
    """Create a Gemini client without exposing credentials in errors."""
    resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not resolved_api_key or not resolved_api_key.strip():
        raise GeminiAdapterError(
            "Missing API key. Set GEMINI_API_KEY or pass api_key.",
            diagnostic_code="AUTHENTICATION_OR_PERMISSION",
            provider_exception_type="MissingAPIKey",
        )

    factory = client_factory or genai.Client

    try:
        return factory(api_key=resolved_api_key)
    except Exception as exc:
        diagnostic_code = _classify_provider_exception(exc)
        exception_type = type(exc).__name__

        raise GeminiAdapterError(
            "Gemini client initialization failed "
            f"({exception_type}; {diagnostic_code}).",
            diagnostic_code=diagnostic_code,
            provider_exception_type=exception_type,
        ) from None


def _normalize_messages(
    messages: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
    """Validate the system/user message structure required by the adapter."""
    if not isinstance(messages, Sequence) or isinstance(
        messages, (str, bytes)
    ):
        raise GeminiAdapterError(
            "Messages must contain exactly one system message "
            "and one user message.",
            diagnostic_code="INVALID_REQUEST",
            provider_exception_type="InvalidMessageStructure",
        )

    system_messages = [
        message
        for message in messages
        if isinstance(message, Mapping)
        and message.get("role") == "system"
    ]
    user_messages = [
        message
        for message in messages
        if isinstance(message, Mapping)
        and message.get("role") == "user"
    ]

    if len(system_messages) != 1 or len(user_messages) != 1:
        raise GeminiAdapterError(
            "Messages must contain exactly one system message "
            "and one user message.",
            diagnostic_code="INVALID_REQUEST",
            provider_exception_type="InvalidMessageStructure",
        )

    system_content = system_messages[0].get("content")
    user_content = user_messages[0].get("content")

    if not isinstance(system_content, str) or not system_content.strip():
        raise GeminiAdapterError(
            "The system message must contain non-empty text.",
            diagnostic_code="INVALID_REQUEST",
            provider_exception_type="InvalidMessageContent",
        )

    if not isinstance(user_content, str) or not user_content.strip():
        raise GeminiAdapterError(
            "The user message must contain non-empty text.",
            diagnostic_code="INVALID_REQUEST",
            provider_exception_type="InvalidMessageContent",
        )

    return system_content, user_content


def create_gemini_callable(
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    client: Any | None = None,
    client_factory: Callable[..., Any] | None = None,
) -> Callable[[Sequence[Mapping[str, Any]]], str]:
    """Create a callable compatible with the provider-neutral evaluator."""
    model_name = _validate_model_name(model)

    if client is not None and client_factory is not None:
        raise ValueError("Provide either client or client_factory, not both.")

    if client is None:
        client = _create_client(api_key, client_factory)

    def call_model(
        messages: Sequence[Mapping[str, Any]],
    ) -> str:
        system_instruction, contents = _normalize_messages(messages)

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    max_output_tokens=1024,
                ),
            )
        except Exception as exc:
            diagnostic_code = _classify_provider_exception(exc)
            exception_type = type(exc).__name__

            raise GeminiAdapterError(
                "Gemini request failed "
                f"({exception_type}; {diagnostic_code}).",
                diagnostic_code=diagnostic_code,
                provider_exception_type=exception_type,
            ) from None

        response_text = getattr(response, "text", None)

        if (
            not isinstance(response_text, str)
            or not response_text.strip()
        ):
            raise GeminiAdapterError(
                "Gemini returned no usable text.",
                diagnostic_code="INVALID_RESPONSE",
                provider_exception_type="EmptyResponse",
            )

        return response_text.strip()

    return call_model


def create_scenario_callable(
    condition: str,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    client: Any | None = None,
    client_factory: Callable[..., Any] | None = None,
) -> Callable[[Mapping[str, Any]], str]:
    """Create a callable that accepts one indirect-injection record."""
    call_model = create_gemini_callable(
        api_key=api_key,
        model=model,
        client=client,
        client_factory=client_factory,
    )

    def call_scenario(record: Mapping[str, Any]) -> str:
        model_input = build_model_input(record)
        messages = build_messages(model_input, condition)
        return call_model(messages)

    return call_scenario
