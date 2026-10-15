
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    ROOT
    / "dataset"
    / "processed"
    / "indirect_injection"
    / "pilot_scenarios.json"
)

OUTPUT_PATH = (
    ROOT
    / "artifacts"
    / "indirect_injection"
    / "linguistic_review_matrix.csv"
)

LANGUAGE_ORDER = ["en", "hi", "mr", "code_mixed"]

# Original scenario fields are preserved for reviewers.
SOURCE_FIELDS = [
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
]

# These fields are intentionally blank for human review.
REVIEW_FIELDS = [
    "reviewer",
    "user_task_semantics",
    "untrusted_content_semantics",
    "action_alignment",
    "naturalness",
    "reviewer_decision",
    "reviewer_notes",
]

CSV_FIELDS = SOURCE_FIELDS + REVIEW_FIELDS


def load_records(path: Path) -> list[dict]:
    """Load the pilot dataset without modifying it."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and isinstance(data.get("scenarios"), list):
        records = data["scenarios"]
    else:
        raise ValueError(
            "Expected a JSON list of scenarios or an object "
            "containing a 'scenarios' list."
        )

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every scenario must be a JSON object.")

    return records


def format_cell(value) -> str:
    """Represent structured values consistently in CSV cells."""
    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
        )

    if value is None:
        return ""

    return str(value)


def build_review_rows(records: list[dict]) -> list[dict]:
    """Build review rows without making linguistic judgments."""
    rows = []

    for record in records:
        row = {
            field: format_cell(record.get(field))
            for field in SOURCE_FIELDS
        }

        # Do not overwrite the dataset's original review status.
        # All reviewer-entered fields start empty.
        for field in REVIEW_FIELDS:
            row[field] = ""

        rows.append(row)

    language_rank = {
        language: index
        for index, language in enumerate(LANGUAGE_ORDER)
    }

    rows.sort(
        key=lambda row: (
            row["scenario_id"],
            language_rank.get(row["language"], len(LANGUAGE_ORDER)),
            row["variant_id"],
        )
    )

    return rows


def write_review_matrix(rows: list[dict], output_path: Path) -> None:
    """Write an Excel-friendly UTF-8 CSV review matrix."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found: {DATASET_PATH}")
        return 1

    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    if not rows:
        print("ERROR: Dataset contains no scenarios.")
        return 1

    variant_ids = [row["variant_id"] for row in rows]
    if len(variant_ids) != len(set(variant_ids)):
        print("ERROR: Duplicate variant_id values found.")
        return 1

    write_review_matrix(rows, OUTPUT_PATH)

    print(f"Source records: {len(records)}")
    print(f"Review rows: {len(rows)}")
    print(f"Output: {OUTPUT_PATH}")
    print("Original dataset: unchanged")
    print("Reviewer judgments: blank")
    print("Approval decisions: not inferred")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
