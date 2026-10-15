
import csv
import json

from scripts.build_linguistic_review_matrix import (
    CSV_FIELDS,
    DATASET_PATH,
    REVIEW_FIELDS,
    SOURCE_FIELDS,
    build_review_rows,
    load_records,
    write_review_matrix,
)


EXPECTED_LANGUAGES = {"en", "hi", "mr", "code_mixed"}


def test_matrix_contains_all_pilot_records():
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    assert len(rows) == 16
    assert len(rows) == len(records)


def test_every_language_is_represented():
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    assert {row["language"] for row in rows} == EXPECTED_LANGUAGES


def test_each_scenario_has_four_language_variants():
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    scenario_ids = {row["scenario_id"] for row in rows}

    assert len(scenario_ids) == 4

    for scenario_id in scenario_ids:
        variants = [
            row for row in rows
            if row["scenario_id"] == scenario_id
        ]

        assert len(variants) == 4
        assert {row["language"] for row in variants} == EXPECTED_LANGUAGES


def test_review_fields_are_blank_and_status_remains_draft():
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    for row in rows:
        assert row["review_status"] == "draft"

        for field in REVIEW_FIELDS:
            assert row[field] == ""


def test_source_fields_are_preserved():
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)

    original_by_id = {
        record["variant_id"]: record
        for record in records
    }

    for row in rows:
        original = original_by_id[row["variant_id"]]

        for field in SOURCE_FIELDS:
            value = original.get(field)

            if isinstance(value, (dict, list)):
                expected = json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            elif value is None:
                expected = ""
            else:
                expected = str(value)

            assert row[field] == expected


def test_csv_output_has_expected_columns_and_rows(tmp_path):
    records = load_records(DATASET_PATH)
    rows = build_review_rows(records)
    output_path = tmp_path / "review_matrix.csv"

    write_review_matrix(rows, output_path)

    with output_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        exported_rows = list(reader)
        exported_fields = reader.fieldnames

    assert exported_fields == CSV_FIELDS
    assert len(exported_rows) == 16
    assert all(row["review_status"] == "draft" for row in exported_rows)
    assert all(
        not row[field]
        for row in exported_rows
        for field in REVIEW_FIELDS
    )
