from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from app.services.avesis.normalizer import NormalizedRecord
from app.services.faculty_catalog import Faculty
from app.services.record_filter import (
    YearScope,
    list_year_matches_year_scope,
    record_matches_year_scope,
)
from app.services.yok.activity_list_parser import (
    parse_activity_list,
)
from app.services.yok.client import (
    YokClient,
    YokRequestError,
)
from app.services.yok.detail_parser import parse_detail_fields
from app.services.yok.normalizer import (
    normalize_activity,
    normalize_publication,
)
from app.services.yok.profile_parser import parse_profile_sections
from app.services.yok.publication_list_parser import (
    parse_publication_list,
)


PUBLICATION_RECORD_TYPES = {
    "article",
    "conference_paper",
    "book",
}

RECORD_TYPE_ORDER = (
    "article",
    "conference_paper",
    "book",
    "project",
    "patent",
)

ProgressCallback = Callable[[int, int | None, str], None]


@dataclass(frozen=True)
class YokCollectionIssue:
    academician_name: str
    record_type: str
    source_url: str
    message: str


@dataclass
class YokCollectionResult:
    records: list[NormalizedRecord] = field(default_factory=list)
    issues: list[YokCollectionIssue] = field(default_factory=list)


class YokReportCollector:
    def __init__(self, client: YokClient) -> None:
        self._client = client

    def collect_records(
        self,
        academicians: Iterable[Faculty],
        selected_record_types: set[str],
        year_scope: YearScope,
        progress_callback: ProgressCallback | None = None,
    ) -> YokCollectionResult:
        result = YokCollectionResult()

        for academician in academicians:
            self._collect_academician_records(
                academician=academician,
                selected_record_types=selected_record_types,
                year_scope=year_scope,
                result=result,
                progress_callback=progress_callback,
            )

        return result

    def _collect_academician_records(
        self,
        *,
        academician: Faculty,
        selected_record_types: set[str],
        year_scope: YearScope,
        result: YokCollectionResult,
        progress_callback: ProgressCallback | None,
    ) -> None:
        if not academician.yok_author_id:
            self._add_issue(
                result=result,
                academician=academician,
                record_type="profile",
                source_url="",
                message="YÖK authorId bilgisi bulunamadı.",
            )
            return

        if not academician.yok_profile_sira:
            self._add_issue(
                result=result,
                academician=academician,
                record_type="profile",
                source_url="",
                message="YÖK profil sira bilgisi bulunamadı.",
            )
            return

        self._notify_progress(
            progress_callback,
            completed=0,
            total=None,
            message=(
                f"{academician.full_name}: "
                "YÖK Akademik profili okunuyor."
            ),
        )

        try:
            profile_page = self._client.open_academician_profile(
                author_id=academician.yok_author_id,
                profile_sira=academician.yok_profile_sira,
            )
            sections = parse_profile_sections(profile_page.html)
        except (YokRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type="profile",
                source_url="https://akademik.yok.gov.tr/AkademikArama/",
                message=str(error),
            )
            return

        for record_type in RECORD_TYPE_ORDER:
            if record_type not in selected_record_types:
                continue

            section_url = sections.get(record_type)

            if section_url is None:
                continue

            self._collect_section_records(
                academician=academician,
                record_type=record_type,
                section_url=section_url,
                profile_url=profile_page.url,
                year_scope=year_scope,
                result=result,
                progress_callback=progress_callback,
            )

    def _collect_section_records(
        self,
        *,
        academician: Faculty,
        record_type: str,
        section_url: str,
        profile_url: str,
        year_scope: YearScope,
        result: YokCollectionResult,
        progress_callback: ProgressCallback | None,
    ) -> None:
        try:
            section_page = self._client.get_html(
                section_url,
                referer_url=profile_url,
            )
        except (YokRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type=record_type,
                source_url=section_url,
                message=str(error),
            )
            return

        if record_type in PUBLICATION_RECORD_TYPES:
            self._collect_publication_section(
                academician=academician,
                record_type=record_type,
                section_url=section_page.url,
                section_html=section_page.html,
                year_scope=year_scope,
                result=result,
                progress_callback=progress_callback,
            )
            return

        self._collect_activity_section(
            academician=academician,
            record_type=record_type,
            section_url=section_page.url,
            section_html=section_page.html,
            year_scope=year_scope,
            result=result,
        )

    def _collect_publication_section(
        self,
        *,
        academician: Faculty,
        record_type: str,
        section_url: str,
        section_html: str,
        year_scope: YearScope,
        result: YokCollectionResult,
        progress_callback: ProgressCallback | None,
    ) -> None:
        try:
            items = parse_publication_list(
                section_html,
                record_type=record_type,
                page_url=section_url,
            )
        except ValueError as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type=record_type,
                source_url=section_url,
                message=str(error),
            )
            return

        selected_items = [
            item
            for item in items
            if list_year_matches_year_scope(
                item.year,
                year_scope,
            )
        ]

        total = len(selected_items)
        seen_detail_dois: set[str] = set()

        self._notify_progress(
            progress_callback,
            completed=0,
            total=total,
            message=(
                f"{academician.full_name}: "
                f"YÖK Akademik'ten {total} kayıt işlenecek."
            ),
        )

        for completed, item in enumerate(
            selected_items,
            start=1,
        ):
            detail_fields: dict[str, str] = {}

            if item.detail_url is not None:
                try:
                    detail_page = self._client.get_html(
                        item.detail_url,
                        referer_url=section_url,
                    )
                    detail_fields = parse_detail_fields(
                        detail_page.html
                    )
                except (YokRequestError, ValueError) as error:
                    self._add_issue(
                        result=result,
                        academician=academician,
                        record_type=record_type,
                        source_url=item.detail_url,
                        message=str(error),
                    )
                    continue

            record = normalize_publication(
                academician_id=academician.id,
                academician_name=academician.full_name,
                item=item,
                detail_fields=detail_fields,
            )

            doi_value = record.data.get("doi")

            if isinstance(doi_value, str):
                normalized_doi = doi_value.strip().casefold() or None
            else:
                normalized_doi = None

            is_duplicate_doi = (
                normalized_doi is not None
                and normalized_doi in seen_detail_dois
            )

            if normalized_doi is not None:
                seen_detail_dois.add(normalized_doi)

            if (
                not is_duplicate_doi
                and record_matches_year_scope(record, year_scope)
            ):
                result.records.append(record)

            self._notify_progress(
                progress_callback,
                completed=completed,
                total=total,
                message=(
                    f"{academician.full_name}: "
                    f"YÖK Akademik {completed}/{total} kayıt işlendi."
                ),
            )

    def _collect_activity_section(
        self,
        *,
        academician: Faculty,
        record_type: str,
        section_url: str,
        section_html: str,
        year_scope: YearScope,
        result: YokCollectionResult,
    ) -> None:
        try:
            items = parse_activity_list(
                section_html,
                record_type=record_type,
            )
        except ValueError as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type=record_type,
                source_url=section_url,
                message=str(error),
            )
            return

        for item in items:
            record = normalize_activity(
                academician_id=academician.id,
                academician_name=academician.full_name,
                item=item,
            )

            if record_matches_year_scope(record, year_scope):
                result.records.append(record)

    @staticmethod
    def _notify_progress(
        progress_callback: ProgressCallback | None,
        *,
        completed: int,
        total: int | None,
        message: str,
    ) -> None:
        if progress_callback is not None:
            progress_callback(completed, total, message)

    @staticmethod
    def _add_issue(
        *,
        result: YokCollectionResult,
        academician: Faculty,
        record_type: str,
        source_url: str,
        message: str,
    ) -> None:
        result.issues.append(
            YokCollectionIssue(
                academician_name=academician.full_name,
                record_type=record_type,
                source_url=source_url,
                message=message,
            )
        )