
import json

import pytest

from backend.app.model_evaluation import (
    ModelOutputError,
    build_messages,
    classify_proposal,
    evaluate_with_callable,
    parse_model_output,
)
from tests.test_indirect_scenario_schema import make_scenario


def valid_output(action=None, **overrides):
    result = {
        "action": action or {"type": "no_action"},
        "task_completed": False,
        "needs_clarification": True,
        "response": "Please clarify the requested action.",
    }
    result.update(overrides)
    return json.dumps(result)


def test_model_messages_exclude_evaluator_labels():
    record = make_scenario()
    messages = build_messages(record, "defense")
    serialized = json.dumps(messages, ensure_ascii=False)

    for secret_field in (
        "expected_action",
        "embedded_attack",
        "expected_security_outcome",
        "expected_task_outcome",
        "review_status",
        "review_notes",
        "source_metadata",
    ):
        assert secret_field not in serialized

    assert record["user_task"] in serialized
    assert record["untrusted_content"] in serialized


def test_unknown_condition_is_rejected():
    with pytest.raises(ValueError):
        build_messages(make_scenario(), "unknown")


def test_malformed_json_is_rejected():
    with pytest.raises(ModelOutputError):
        parse_model_output("not json")


@pytest.mark.parametrize("raw", [
    "[]",
    '{"action":{"type":"no_action"}}',
    '{"action":{"type":"no_action"},"task_completed":1,'
    '"needs_clarification":true,"response":"x"}',
    '{"action":{"type":"no_action"},"task_completed":false,'
    '"needs_clarification":true,"response":"x","extra":1}',
])
def test_invalid_response_shapes_are_rejected(raw):
    with pytest.raises(ModelOutputError):
        parse_model_output(raw)


def test_unknown_tool_is_rejected():
    output = valid_output({
        "tool_name": "delete_file",
        "arguments": {},
    })
    with pytest.raises(ModelOutputError):
        parse_model_output(output)


def test_invalid_tool_arguments_are_rejected():
    output = valid_output({
        "tool_name": "send_message",
        "arguments": {"recipient": "attacker@example.test"},
    })
    with pytest.raises(ModelOutputError):
        parse_model_output(output)


def test_sensitive_proposal_is_classified_but_not_executed():
    record = make_scenario()
    parsed = parse_model_output(valid_output({
        "tool_name": "read_private_note",
        "arguments": {"note_id": "demo"},
    }))

    result = classify_proposal(parsed, record)

    assert result["sensitive_action_attempt"] is True
    assert result["executed"] is False



def test_callable_is_injected_and_no_tool_is_executed():
    record = make_scenario()
    calls = []

    def fake_model(messages):
        calls.append(messages)
        return valid_output()

    result = evaluate_with_callable(record, "baseline", fake_model)

    assert len(calls) == 1
    assert result["output_valid"] is True
    assert result["executed"] is False
    assert "raw_output" not in result


def test_callable_raw_output_can_be_retained_explicitly():
    record = make_scenario()
    raw = valid_output()

    result = evaluate_with_callable(
        record,
        "baseline",
        lambda messages: raw,
        retain_raw_output=True,
    )

    assert result["raw_output"] == raw

def test_callable_raw_output_is_omitted_by_default():
    record = make_scenario()

    result = evaluate_with_callable(
        record,
        "baseline",
        lambda messages: valid_output(),
    )

    assert result["output_valid"] is True
    assert "raw_output" not in result


def test_callable_raw_output_can_be_retained_explicitly():
    record = make_scenario()
    raw = valid_output()

    result = evaluate_with_callable(
        record,
        "baseline",
        lambda messages: raw,
        retain_raw_output=True,
    )

    assert result["raw_output"] == raw
    assert result["executed"] is False
