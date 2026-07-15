from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.services.avesis.normalizer import NormalizedRecord


@dataclass(frozen=True)
class YearScope:
    start_year: int | None = None
    end_year: int | None = None

    def __post_init__(self) -> None:
        has_start_year = self.start_year is not None
        has_end_year = self.end_year is not None

        if has_start_year != has_end_year:
            raise ValueError(
                "Yıl aralığında başlangıç ve bitiş yılı birlikte verilmelidir."
            )

        if (
            self.start_year is not None
            and self.end_year is not None
            and self.start_year > self.end_year
        ):
            raise ValueError(
                "Başlangıç yılı bitiş yılından büyük olamaz."
            )

    @classmethod
    def single_year(cls, year: int) -> YearScope:
        return cls(start_year=year, end_year=year)

    @classmethod
    def all_years(cls) -> YearScope:
        return cls()

    @property
    def is_all_years(self) -> bool:
        return self.start_year is None

    def contains(self, year: int) -> bool:
        if self.is_all_years:
            return True

        return self.start_year <= year <= self.end_year


def list_year_matches_year_scope(
    year: int | None,
    year_scope: YearScope,
) -> bool:
    if year_scope.is_all_years:
        return True

    if year is None:
        return True

    return year_scope.contains(year)


def filter_records(
    records: Iterable[NormalizedRecord],
    year_scope: YearScope,
) -> list[NormalizedRecord]:
    return [
        record
        for record in records
        if record_matches_year_scope(record, year_scope)
    ]


def record_matches_year_scope(
    record: NormalizedRecord,
    year_scope: YearScope,
) -> bool:
    if year_scope.is_all_years:
        return True

    if record.record_type == "project":
        return _project_matches_year_scope(record, year_scope)

    return list_year_matches_year_scope(
        record.year,
        year_scope,
    )


def _project_matches_year_scope(
    record: NormalizedRecord,
    year_scope: YearScope,
) -> bool:
    start_year = _as_year(record.data.get("start_year"))
    end_year = _as_year(record.data.get("end_year"))

    if start_year is None and end_year is None:
        return True

    start_year = start_year or end_year
    end_year = end_year or start_year

    return not (
        end_year < year_scope.start_year
        or start_year > year_scope.end_year
    )


def _as_year(value: object) -> int | None:
    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.isdigit():
        return int(value)

    return None