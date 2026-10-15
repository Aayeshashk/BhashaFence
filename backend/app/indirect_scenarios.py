"""Validation helpers for the separate indirect-injection pilot.

No model calls, external services, or tool execution occur here.
The existing 24-scenario structured-action dataset is not modified.
"""

from collections import defaultdict
from typing import Any


LANGUAGES = frozenset({"en", "hi", "mr", "code_mixed"})

SCENARIO_CATEGORIES = frozenset({
    "benign",
    "embedded_attack",
    "ambiguous_input",
})

REVIEW_STATUSES = frozenset({"draft", "reviewed", "approved"})

SOURCE_LABELS = frozenset({"user", "untrusted_content"})

TOOL_ARGUMENT_TYPES: dict[str, dict[str, type]] = {
    "search_public": {"query": str},
    "read_public_document": {"document_id": str},
    "read_private_note": {"note_id": str},
    "send_message": {"recipient": str, "message": str},
}

REQUIRED_FIELDS = frozenset({
    "scenario_id",
    "variant_id",
    "language",
    "scenario_category",
    "user_task",
    "untrusted_content",
    "source_metadata",
    "expected_action",
    "embedded_attack",
    "expected_security_outcome",
    "expected_task_outcome",
    "review_status",
    "review_notes",
})

EVALUATOR_ONLY_FIELDS = frozenset({
    "expected_action",
    "embedded_attack",
    "expected_security_outcome",
    "expected_task_outcome",
    "review_status",
    "review_notes",
})

STRING_FIELDS = (
    "scenario_id",
    "variant_id",
    "user_task",
    "untrusted_content",
    "expected_security_outcome",
    "expected_task_outcome",
)


def validate_expected_action(
    action: Any,
    location: str,
) -> list[str]:
    """Validate a reference action against the current simulator schema."""
    errors: list[str] = []

    if not isinstance(action, dict):
        return [f"{location}: expected_action must be an object"]

    if action.get("type") == "no_action":
        if set(action) != {"type"}:
            errors.append(
                f"{location}: no_action must contain only the type field"
            )
        return errors

    if set(action) != {"tool_name", "arguments"}:
        errors.append(
            f"{location}: expected_action must contain exactly "
            "tool_name and arguments, or type=no_action"
        )
        return errors

    tool_name = action["tool_name"]
    arguments = action["arguments"]

    if not isinstance(tool_name, str):
        errors.append(f"{location}: tool_name must be a string")
        return errors

    if tool_name not in TOOL_ARGUMENT_TYPES:
        errors.append(
            f"{location}: unsupported tool_name {tool_name!r}"
        )
        return errors

    if not isinstance(arguments, dict):
        errors.append(f"{location}: arguments must be an object")
        return errors

    expected_arguments = TOOL_ARGUMENT_TYPES[tool_name]

    if set(arguments) != set(expected_arguments):
        errors.append(
            f"{location}: {tool_name} requires exactly these "
            f"argument keys: {sorted(expected_arguments)}"
        )
        return errors

    for argument_name, expected_type in expected_arguments.items():
        value = arguments[argument_name]

        # Use exact type checks to avoid accepting bool as int
        # if non-string argument types are introduced later.
        if type(value) is not expected_type:
            errors.append(
                f"{location}: argument {argument_name!r} must be "
                f"{expected_type.__name__}"
            )
        elif isinstance(value, str) and not value.strip():
            errors.append(
                f"{location}: argument {argument_name!r} cannot be empty"
            )

    return errors


def validate_scenarios(records: Any) -> list[str]:
    """Return all detected schema errors; an empty list means valid."""
    if not isinstance(records, list):
        return ["dataset: top-level value must be a list"]

    errors: list[str] = []
    seen_variant_ids: set[str] = set()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for index, record in enumerate(records):
        location = f"record[{index}]"

        if not isinstance(record, dict):
            errors.append(f"{location}: record must be an object")
            continue

        missing = REQUIRED_FIELDS - set(record)
        if missing:
            errors.append(
                f"{location}: missing fields {sorted(missing)}"
            )

        for field_name in STRING_FIELDS:
            if field_name in record:
                value = record[field_name]
                if not isinstance(value, str) or not value.strip():
                    errors.append(
                        f"{location}: {field_name} must be a "
                        "non-empty string"
                    )

        for field_name in ("scenario_id", "variant_id"):
            value = record.get(field_name)
            if not isinstance(value, str) or not value.strip():
                continue

            if field_name == "variant_id":
                if value in seen_variant_ids:
                    errors.append(
                        f"{location}: duplicate variant_id {value!r}"
                    )
                seen_variant_ids.add(value)

        language = record.get("language")
        if not isinstance(language, str) or language not in LANGUAGES:
            errors.append(
                f"{location}: unsupported language {language!r}"
            )

        category = record.get("scenario_category")
        if (
            not isinstance(category, str)
            or category not in SCENARIO_CATEGORIES
        ):
            errors.append(
                f"{location}: unsupported scenario_category "
                f"{category!r}"
            )

        source = record.get("source_metadata")
        if not isinstance(source, str) or source not in SOURCE_LABELS:
            errors.append(
                f"{location}: unsupported source_metadata {source!r}"
            )

        attack = record.get("embedded_attack")
        if type(attack) is not bool:
            errors.append(
                f"{location}: embedded_attack must be a boolean"
            )
        elif category == "benign" and attack:
            errors.append(
                f"{location}: benign scenarios cannot contain "
                "an embedded attack"
            )
        elif category == "embedded_attack" and not attack:
            errors.append(
                f"{location}: embedded_attack scenarios must "
                "declare embedded_attack=true"
            )

        review_status = record.get("review_status")
        if (
            not isinstance(review_status, str)
            or review_status not in REVIEW_STATUSES
        ):
            errors.append(
                f"{location}: unsupported review_status "
                f"{review_status!r}"
            )

        if "expected_action" in record:
            errors.extend(
                validate_expected_action(
                    record["expected_action"],
                    location,
                )
            )

        if "review_notes" in record and not isinstance(
            record["review_notes"], str
        ):
            errors.append(
                f"{location}: review_notes must be a string"
            )

        scenario_id = record.get("scenario_id")
        if isinstance(scenario_id, str) and scenario_id.strip():
            groups[scenario_id].append(record)

    # Matched variants must describe the same underlying experiment.
    # Their natural-language text and variant IDs may differ.
    invariant_fields = (
        "scenario_category",
        "source_metadata",
        "embedded_attack",
        "expected_action",
        "expected_security_outcome",
        "expected_task_outcome",
    )

    for scenario_id, variants in groups.items():
        if len(variants) < 2:
            continue

        reference = variants[0]

        for variant in variants[1:]:
            for field_name in invariant_fields:
                if (
                    field_name in reference
                    and field_name in variant
                    and reference[field_name] != variant[field_name]
                ):
                    errors.append(
                        f"scenario {scenario_id!r}: matched variants "
                        f"disagree on {field_name!r}"
                    )

    return errors


def build_model_input(record: dict[str, Any]) -> dict[str, str]:
    """Return only the scenario content intended for the agent.

    Provenance must be supplied separately by the trusted harness.
    Evaluator labels must never be included in this object.
    """
    return {
        "user_task": record["user_task"],
        "untrusted_content": record["untrusted_content"],
    }