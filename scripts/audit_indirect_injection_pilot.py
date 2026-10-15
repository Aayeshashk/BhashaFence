
"""Run deterministic quality checks on the indirect-injection pilot."""

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = (
    ROOT / "dataset" / "processed" / "indirect_injection"
    / "pilot_scenarios.json"
)
REPORT_PATH = (
    ROOT / "artifacts" / "indirect_injection"
    / "pilot_quality_audit.json"
)

EXPECTED_LANGUAGES = {"en", "hi", "mr", "code_mixed"}
EXPECTED_SCENARIOS = {"S1", "S2", "S3", "S4"}
EXPECTED_VARIANTS = {
    f"{scenario}-{language}"
    for scenario in EXPECTED_SCENARIOS
    for language in EXPECTED_LANGUAGES
}


def audit_dataset(records):
    """Return deterministic structural and consistency findings."""
    errors = []
    warnings = []
    groups = defaultdict(list)

    if not isinstance(records, list):
        return {
            "passed": False,
            "record_count": 0,
            "errors": ["Dataset root must be a list."],
            "warnings": [],
            "scenario_summary": {},
        }

    variant_ids = [
        record.get("variant_id")
        for record in records
        if isinstance(record, dict)
    ]
    duplicates = [
        variant_id
        for variant_id, count in Counter(variant_ids).items()
        if count > 1
    ]

    if len(records) != 16:
        errors.append(f"Expected 16 records; found {len(records)}.")

    if len(set(variant_ids)) != len(variant_ids):
        errors.append(f"Duplicate variant IDs: {duplicates}")

    actual_variants = set(variant_ids)
    if actual_variants != EXPECTED_VARIANTS:
        errors.append(
            "Variant IDs do not match the expected 4 scenarios "
            "x 4 languages."
        )

    for index, record in enumerate(records):
        location = f"record[{index}]"

        if not isinstance(record, dict):
            errors.append(f"{location}: record must be an object.")
            continue

        scenario_id = record.get("scenario_id")
        if isinstance(scenario_id, str):
            groups[scenario_id].append(record)

        if record.get("language") not in EXPECTED_LANGUAGES:
            errors.append(f"{location}: unsupported language.")

        if record.get("review_status") != "draft":
            errors.append(
                f"{location}: pilot records must remain draft."
            )

        if record.get("source_metadata") != "untrusted_content":
            errors.append(
                f"{location}: source metadata must identify "
                "the untrusted content."
            )

        if not isinstance(record.get("user_task"), str) or not (
            record["user_task"].strip()
        ):
            errors.append(f"{location}: missing user task.")

        if not isinstance(
            record.get("untrusted_content"), str
        ) or not record["untrusted_content"].strip():
            errors.append(f"{location}: missing untrusted content.")

        category = record.get("scenario_category")
        attack = record.get("embedded_attack")

        if category == "benign" and attack is not False:
            errors.append(
                f"{location}: benign scenario must set "
                "embedded_attack=false."
            )

        if category == "embedded_attack" and attack is not True:
            errors.append(
                f"{location}: embedded attack must be marked true."
            )

        if category == "ambiguous_input":
            if attack is not False:
                errors.append(
                    f"{location}: ambiguous input must not be "
                    "labelled an embedded attack."
                )
            action = record.get("expected_action")
            if action != {"type": "no_action"}:
                errors.append(
                    f"{location}: ambiguous input should expect no action."
                )

        # The user task and untrusted content must remain separate fields.
        # This check reports suspicious exact duplication only; it does not
        # attempt to infer natural-language meaning.
        if (
            record.get("user_task", "").strip()
            == record.get("untrusted_content", "").strip()
        ):
            warnings.append(
                f"{location}: user task exactly matches untrusted content."
            )

    scenario_summary = {}

    invariant_fields = (
        "scenario_category",
        "source_metadata",
        "expected_action",
        "embedded_attack",
        "expected_security_outcome",
        "expected_task_outcome",
    )

    for scenario_id in sorted(EXPECTED_SCENARIOS):
        variants = groups.get(scenario_id, [])
        languages = {
            record.get("language") for record in variants
        }

        scenario_summary[scenario_id] = {
            "variant_count": len(variants),
            "languages": sorted(
                language
                for language in languages
                if isinstance(language, str)
            ),
            "all_draft": all(
                record.get("review_status") == "draft"
                for record in variants
            ),
        }

        if len(variants) != 4:
            errors.append(
                f"{scenario_id}: expected 4 variants; "
                f"found {len(variants)}."
            )

        if languages != EXPECTED_LANGUAGES:
            errors.append(
                f"{scenario_id}: expected one variant per language."
            )

        if variants:
            reference = variants[0]
            for variant in variants[1:]:
                for field in invariant_fields:
                    if reference.get(field) != variant.get(field):
                        errors.append(
                            f"{scenario_id}: variants disagree on {field}."
                        )

    # These checks cannot prove that translations preserve meaning.
    warnings.append(
        "Human linguistic review is required for semantic equivalence."
    )
    warnings.append(
        "No natural-language understanding or model resistance is "
        "measured by this structural audit."
    )

    return {
        "passed": not errors,
        "record_count": len(records),
        "scenario_count": len(groups),
        "language_count": len(
            {
                record.get("language")
                for record in records
                if isinstance(record, dict)
            }
        ),
        "errors": errors,
        "warnings": warnings,
        "scenario_summary": scenario_summary,
    }


def main():
    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found: {DATASET_PATH}")

    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    report = audit_dataset(records)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Records audited: {report['record_count']}")
    print(f"Structural audit: {'PASSED' if report['passed'] else 'FAILED'}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")

    for error in report["errors"]:
        print(f"ERROR: {error}")

    for warning in report["warnings"]:
        print(f"REVIEW NOTE: {warning}")

    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
