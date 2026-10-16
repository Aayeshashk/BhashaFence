
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app.gemini_adapter import (
    DEFAULT_MODEL,
    GeminiAdapterError,
    _classify_provider_exception,
    create_gemini_callable,
    create_scenario_callable,
)
from tests.test_indirect_scenario_schema import make_scenario


def fake_client(
    response_text='{"action":{"type":"no_action"},'
    '"task_completed":false,'
    '"needs_clarification":true,'
    '"response":"Please clarify."}'
):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        text=response_text
    )
    return client


def test_creates_client_from_explicit_api_key():
    client = fake_client()
    factory = Mock(return_value=client)

    create_gemini_callable(
        api_key="test-key-not-real",
        client_factory=factory,
    )

    factory.assert_called_once_with(api_key="test-key-not-real")


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(GeminiAdapterError, match="Missing API key"):
        create_gemini_callable()


def test_empty_model_name_is_rejected():
    with pytest.raises(ValueError, match="model"):
        create_gemini_callable(model=" ")


def test_request_uses_json_mode_and_system_instruction():
    client = fake_client()
    call_model = create_gemini_callable(
        model="test-model",
        client=client,
    )

    messages = [
        {"role": "system", "content": "Follow the evaluation policy."},
        {"role": "user", "content": '{"user_task":"test"}'},
    ]

    result = call_model(messages)

    assert result.startswith('{"action"')
    client.models.generate_content.assert_called_once()

    kwargs = client.models.generate_content.call_args.kwargs

    assert kwargs["model"] == "test-model"
    assert kwargs["contents"] == '{"user_task":"test"}'
    assert kwargs["config"].system_instruction == (
        "Follow the evaluation policy."
    )
    assert kwargs["config"].response_mime_type == "application/json"
    assert kwargs["config"].max_output_tokens == 1024


def test_invalid_message_structure_is_rejected_without_request():
    client = fake_client()
    call_model = create_gemini_callable(client=client)

    with pytest.raises(GeminiAdapterError, match="exactly one"):
        call_model([{"role": "user", "content": "hello"}])

    client.models.generate_content.assert_not_called()


@pytest.mark.parametrize("response_text", ["", "   ", None])
def test_missing_response_text_is_rejected(response_text):
    client = fake_client()
    client.models.generate_content.return_value = SimpleNamespace(
        text=response_text
    )

    call_model = create_gemini_callable(client=client)

    with pytest.raises(GeminiAdapterError, match="no usable text"):
        call_model([
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ])


def test_provider_error_is_sanitized():
    client = fake_client()
    client.models.generate_content.side_effect = RuntimeError(
        "secret-key-and-private-response"
    )

    call_model = create_gemini_callable(client=client)

    with pytest.raises(
        GeminiAdapterError,
        match="RuntimeError",
    ) as error:
        call_model([
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ])

    assert "secret-key-and-private-response" not in str(error.value)


def test_scenario_callable_uses_existing_message_builder():
    client = fake_client()
    call_scenario = create_scenario_callable(
        "baseline",
        client=client,
    )

    result = call_scenario(make_scenario())

    assert result.startswith('{"action"')
    client.models.generate_content.assert_called_once()


def test_default_model_is_configurable():
    assert isinstance(DEFAULT_MODEL, str)
    assert DEFAULT_MODEL


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (TimeoutError("request timed out"), "TIMEOUT"),
        (
            RuntimeError("HTTP 429: quota exceeded"),
            "RATE_LIMIT_OR_QUOTA",
        ),
        (
            RuntimeError("HTTP 503: server error"),
            "PROVIDER_SERVER_ERROR",
        ),
        (
            RuntimeError("HTTP 401: unauthorized"),
            "AUTHENTICATION_OR_PERMISSION",
        ),
        (
            RuntimeError("HTTP 400: invalid request"),
            "INVALID_REQUEST",
        ),
        (ConnectionError("connection failed"), "NETWORK_ERROR"),
        (
            RuntimeError("request failed with reference 15003"),
            "OTHER_PROVIDER_ERROR",
        ),
    ],
)
def test_provider_exception_classification(exception, expected):
    assert _classify_provider_exception(exception) == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("HTTP 500: internal error", "PROVIDER_SERVER_ERROR"),
        ("HTTP 502: bad gateway", "PROVIDER_SERVER_ERROR"),
        ("HTTP 504: gateway timeout", "PROVIDER_SERVER_ERROR"),
        ("reference 15003", "OTHER_PROVIDER_ERROR"),
        ("reference 40123", "OTHER_PROVIDER_ERROR"),
        ("reference 42999", "OTHER_PROVIDER_ERROR"),
    ],
)
def test_status_classification_does_not_match_numeric_substrings(
    message,
    expected,
):
    assert _classify_provider_exception(RuntimeError(message)) == expected


# Diagnostic metadata validation regression tests.


@pytest.mark.parametrize(
    "diagnostic_code",
    [
        "UNKNOWN_CODE",
        "",
        "HTTP 500: private details",
        None,
        123,
    ],
)
def test_invalid_diagnostic_code_falls_back_to_safe_default(
    diagnostic_code,
):
    error = GeminiAdapterError(
        "Safe error",
        diagnostic_code=diagnostic_code,
    )

    assert error.diagnostic_code == "OTHER_PROVIDER_ERROR"


@pytest.mark.parametrize(
    "provider_exception_type",
    [
        "RuntimeError: secret details",
        "",
        "Exception\nprivate details",
        "A" * 65,
        None,
        123,
    ],
)
def test_invalid_provider_exception_type_falls_back_to_safe_default(
    provider_exception_type,
):
    error = GeminiAdapterError(
        "Safe error",
        provider_exception_type=provider_exception_type,
    )

    assert error.provider_exception_type == "Exception"


def test_valid_diagnostic_metadata_is_preserved():
    error = GeminiAdapterError(
        "Safe error",
        diagnostic_code="NETWORK_ERROR",
        provider_exception_type="ConnectionError",
    )

    assert error.diagnostic_code == "NETWORK_ERROR"
    assert error.provider_exception_type == "ConnectionError"
