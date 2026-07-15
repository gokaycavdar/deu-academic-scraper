from app.services.avesis.normalizer import NormalizedRecord
from app.services.record_filter import (
    YearScope,
    filter_records,
    record_matches_year_scope,
)


def make_record(
    *,
    record_id: str,
    record_type: str = "article",
    year: int | None,
    data: dict[str, str | int | None] | None = None,
) -> NormalizedRecord:
    return NormalizedRecord(
        academician_id="test-academician",
        academician_name="Test Akademisyen",
        record_id=record_id,
        record_type=record_type,
        title="Test Kaydı",
        contributor_names="",
        contributor_text="",
        source_url="https://example.com/record",
        citation_text="",
        year=year,
        data=data or {},
    )


def test_single_year_keeps_matching_and_undated_records() -> None:
    records = [
        make_record(record_id="2025", year=2025),
        make_record(record_id="2026", year=2026),
        make_record(record_id="unknown", year=None),
    ]

    filtered_records = filter_records(
        records,
        YearScope.single_year(2026),
    )

    assert [
        record.record_id
        for record in filtered_records
    ] == ["2026", "unknown"]


def test_project_is_kept_when_its_dates_overlap_range() -> None:
    project = make_record(
        record_id="project-overlap",
        record_type="project",
        year=2024,
        data={
            "start_year": 2024,
            "end_year": 2026,
        },
    )

    assert record_matches_year_scope(
        project,
        YearScope.single_year(2025),
    )


def test_project_is_excluded_when_dates_do_not_overlap_range() -> None:
    project = make_record(
        record_id="project-old",
        record_type="project",
        year=2018,
        data={
            "start_year": 2018,
            "end_year": 2020,
        },
    )

    assert not record_matches_year_scope(
        project,
        YearScope.single_year(2026),
    )