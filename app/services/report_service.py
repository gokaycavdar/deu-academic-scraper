from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from app.services.avesis.client import (
    AvesisClient,
    AvesisRequestError,
)
from app.services.avesis.detail_parser import parse_detail_page
from app.services.avesis.list_parser import (
    PublicationListItem,
    parse_publication_list,
)
from app.services.avesis.normalizer import (
    NormalizedRecord,
    normalize_activity,
    normalize_publication,
)
from app.services.avesis.project_list_parser import (
    ActivityListItem,
    parse_project_list,
)
from app.services.faculty_catalog import Faculty
from app.services.record_filter import (
    YearScope,
    list_year_matches_year_scope,
    record_matches_year_scope,
)


SUPPORTED_RECORD_TYPES = {
    "article",
    "conference_paper",
    "book",
    "project",
    "patent",
}

PUBLICATION_RECORD_TYPES = {
    "article",
    "conference_paper",
    "book",
}

ACTIVITY_RECORD_TYPES = {
    "project",
    "patent",
}

ProgressCallback = Callable[[int, int | None, str], None]
DetailItem = PublicationListItem | ActivityListItem


@dataclass(frozen=True)
class ReportIssue:
    academician_name: str
    record_type: str
    source_url: str
    message: str


@dataclass
class ReportResult:
    records: list[NormalizedRecord] = field(default_factory=list)
    issues: list[ReportIssue] = field(default_factory=list)


@dataclass(frozen=True)
class DetailWorkItem:
    academician: Faculty
    item: DetailItem


class ReportService:
    def __init__(self, client: AvesisClient) -> None:
        self._client = client

    def collect_records(
        self,
        academicians: Iterable[Faculty],
        selected_record_types: set[str],
        year_scope: YearScope,
        progress_callback: ProgressCallback | None = None,
    ) -> ReportResult:
        self._validate_record_types(selected_record_types)

        result = ReportResult()
        academician_list = list(academicians)

        self._notify_progress(
            progress_callback,
            completed=0,
            total=None,
            message="AVESİS kayıt listeleri okunuyor.",
        )

        work_items = self._build_detail_work_items(
            academicians=academician_list,
            selected_record_types=selected_record_types,
            year_scope=year_scope,
            result=result,
            progress_callback=progress_callback,
        )

        total = len(work_items)

        self._notify_progress(
            progress_callback,
            completed=0,
            total=total,
            message=f"{total} kayıt detayı okunacak.",
        )

        for completed, work_item in enumerate(work_items, start=1):
            self._collect_detail_work_item(
                work_item=work_item,
                year_scope=year_scope,
                result=result,
            )

            self._notify_progress(
                progress_callback,
                completed=completed,
                total=total,
                message=(
                    f"{work_item.academician.full_name}: "
                    f"{completed}/{total} kayıt işlendi."
                ),
            )

        return result

    def _build_detail_work_items(
        self,
        academicians: list[Faculty],
        selected_record_types: set[str],
        year_scope: YearScope,
        result: ReportResult,
        progress_callback: ProgressCallback | None,
    ) -> list[DetailWorkItem]:
        work_items: list[DetailWorkItem] = []

        for academician in academicians:
            if selected_record_types & PUBLICATION_RECORD_TYPES:
                self._notify_progress(
                    progress_callback,
                    completed=0,
                    total=None,
                    message=(
                        f"{academician.full_name}: "
                        "yayın listesi okunuyor."
                    ),
                )

                work_items.extend(
                    self._get_publication_work_items(
                        academician=academician,
                        selected_record_types=selected_record_types,
                        year_scope=year_scope,
                        result=result,
                    )
                )

            if selected_record_types & ACTIVITY_RECORD_TYPES:
                self._notify_progress(
                    progress_callback,
                    completed=0,
                    total=None,
                    message=(
                        f"{academician.full_name}: "
                        "proje ve patent listesi okunuyor."
                    ),
                )

                work_items.extend(
                    self._get_activity_work_items(
                        academician=academician,
                        selected_record_types=selected_record_types,
                        result=result,
                    )
                )

        return work_items

    def _get_publication_work_items(
        self,
        academician: Faculty,
        selected_record_types: set[str],
        year_scope: YearScope,
        result: ReportResult,
    ) -> list[DetailWorkItem]:
        try:
            list_page = self._client.get_publications(
                academician.profile_url
            )
            items = parse_publication_list(list_page.html)
        except (AvesisRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type="publication_list",
                source_url=academician.profile_url,
                message=str(error),
            )
            return []

        return [
            DetailWorkItem(
                academician=academician,
                item=item,
            )
            for item in items
            if (
                item.record_type.value in selected_record_types
                and list_year_matches_year_scope(
                    item.year,
                    year_scope,
                )
            )
        ]

    def _get_activity_work_items(
        self,
        academician: Faculty,
        selected_record_types: set[str],
        result: ReportResult,
    ) -> list[DetailWorkItem]:
        try:
            list_page = self._client.get_projects(
                academician.profile_url
            )
            items = parse_project_list(list_page.html)
        except (AvesisRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=academician,
                record_type="activity_list",
                source_url=academician.profile_url,
                message=str(error),
            )
            return []

        return [
            DetailWorkItem(
                academician=academician,
                item=item,
            )
            for item in items
            if item.record_type.value in selected_record_types
        ]

    def _collect_detail_work_item(
        self,
        work_item: DetailWorkItem,
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
        if isinstance(work_item.item, PublicationListItem):
            self._collect_publication_detail(
                work_item=work_item,
                year_scope=year_scope,
                result=result,
            )
            return

        self._collect_activity_detail(
            work_item=work_item,
            year_scope=year_scope,
            result=result,
        )

    def _collect_publication_detail(
        self,
        work_item: DetailWorkItem,
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
        item = work_item.item

        if not isinstance(item, PublicationListItem):
            raise TypeError("Yayın detay öğesi bekleniyordu.")

        try:
            detail_page = self._client.get_html(item.detail_url)
            detail = parse_detail_page(detail_page.html)

            record = normalize_publication(
                academician_id=work_item.academician.id,
                academician_name=work_item.academician.full_name,
                item=item,
                detail=detail,
            )
        except (AvesisRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=work_item.academician,
                record_type=item.record_type.value,
                source_url=item.detail_url,
                message=str(error),
            )
            return

        if record_matches_year_scope(record, year_scope):
            result.records.append(record)

    def _collect_activity_detail(
        self,
        work_item: DetailWorkItem,
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
        item = work_item.item

        if not isinstance(item, ActivityListItem):
            raise TypeError("Proje veya patent detay öğesi bekleniyordu.")

        try:
            detail_page = self._client.get_html(item.detail_url)
            detail = parse_detail_page(detail_page.html)

            record = normalize_activity(
                academician_id=work_item.academician.id,
                academician_name=work_item.academician.full_name,
                item=item,
                detail=detail,
            )
        except (AvesisRequestError, ValueError) as error:
            self._add_issue(
                result=result,
                academician=work_item.academician,
                record_type=item.record_type.value,
                source_url=item.detail_url,
                message=str(error),
            )
            return

        if record_matches_year_scope(record, year_scope):
            result.records.append(record)

    @staticmethod
    def _validate_record_types(
        selected_record_types: set[str],
    ) -> None:
        if not selected_record_types:
            raise ValueError(
                "En az bir kayıt türü seçilmelidir."
            )

        unknown_types = selected_record_types - SUPPORTED_RECORD_TYPES

        if unknown_types:
            unknown = ", ".join(sorted(unknown_types))
            raise ValueError(
                f"Desteklenmeyen kayıt türleri seçildi: {unknown}"
            )

    @staticmethod
    def _notify_progress(
        progress_callback: ProgressCallback | None,
        *,
        completed: int,
        total: int | None,
        message: str,
    ) -> None:
        if progress_callback is None:
            return

        progress_callback(completed, total, message)

    @staticmethod
    def _add_issue(
        result: ReportResult,
        academician: Faculty,
        record_type: str,
        source_url: str,
        message: str,
    ) -> None:
        result.issues.append(
            ReportIssue(
                academician_name=academician.full_name,
                record_type=record_type,
                source_url=source_url,
                message=message,
            )
        )