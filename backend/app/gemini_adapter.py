"""Gemini API adapter for the BhashaFence model-evaluation harness.

This adapter only requests model output. It never executes proposed tools.
Tests can inject a fake client to avoid network calls.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from backend.app.model_evaluation import build_messages


DEFAULT_MODEL = "gemini-3.1-flash-lite"
MAX_OUTPUT_TOKENS = 1024


class GeminiAdapterError(RuntimeError):
    """Raised when Gemini cannot provide usable text output."""


def _extract_text(response: Any) -> str:
    """Extract generated text without exposing response internals in errors."""
    text = getattr(response, "text", None)

    if not isinstance(text, str) or not text.strip():
        raise GeminiAdapterError("Gemini returned no usable text output.")

    return text


def create_gemini_callable(
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client: Any | None = None,
    client_factory: Callable[..., Any] | None = None,
) -> Callable[[list[dict[str, str]]], str]:
    """Create a callable compatible with the existing model runner.

    Supply a fake ``client`` in tests. Without a client, the SDK is imported
    lazily and the API key is taken from the argument or GEMINI_API_KEY.
    No request is made until the returned callable is invoked.
    """
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string.")

    if client is None:
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise GeminiAdapterError(
                "Missing API key. Set GEMINI_API_KEY before creating "
                "a live Gemini client."
            )

        if client_factory is None:
            try:
                from google import genai
            except ImportError as exc:
                raise GeminiAdapterError(
                    "Gemini SDK is not installed. Install requirements-model.txt."
                ) from exc

            client_factory = genai.Client

        client = client_factory(api_key=resolved_key)

    def call_model(messages: list[dict[str, str]]) -> str:
        system_messages = [
            item["content"]
            for item in messages
            if item.get("role") == "system"
        ]
        user_messages = [
            item["content"]
            for item in messages
            if item.get("role") == "user"
        ]

        if len(system_messages) != 1 or len(user_messages) != 1:
            raise GeminiAdapterError(
                "Expected exactly one system message and one user message."
            )

        try:
            from google.genai import types

            response = client.models.generate_content(
                model=model,
                contents=user_messages[0],
                config=types.GenerateContentConfig(
                    system_instruction=system_messages[0],
                    response_mime_type="application/json",
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                ),
            )
        except GeminiAdapterError:
            raise
        except Exception as exc:
            # Keep credentials and provider response details out of reports.
            raise GeminiAdapterError(
                f"Gemini request failed ({type(exc).__name__})."
            ) from None

        return _extract_text(response)

    return call_model


def create_scenario_callable(
    condition: str,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client: Any | None = None,
    client_factory: Callable[..., Any] | None = None,
) -> Callable[[dict[str, Any]], str]:
    """Create a scenario-level callable using the existing message builder."""
    provider_callable = create_gemini_callable(
        model=model,
        api_key=api_key,
        client=client,
        client_factory=client_factory,
    )

    def call_scenario(record: dict[str, Any]) -> str:
        return provider_callable(build_messages(record, condition))

    return call_scenario