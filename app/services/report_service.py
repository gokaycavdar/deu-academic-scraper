from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from app.services.avesis.client import (
    AvesisClient,
    AvesisRequestError,
)
from app.services.avesis.detail_parser import parse_detail_page
from app.services.avesis.list_parser import parse_publication_list
from app.services.avesis.normalizer import (
    NormalizedRecord,
    normalize_activity,
    normalize_publication,
)
from app.services.avesis.project_list_parser import parse_project_list
from app.services.faculty_catalog import Faculty
from app.services.record_filter import (
    YearScope,
    record_matches_year_scope,
)


SUPPORTED_RECORD_TYPES = {
    "article",
    "conference_paper",
    "book",
    "project",
    "patent",
}


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


class ReportService:
    def __init__(self, client: AvesisClient) -> None:
        self._client = client

    def collect_records(
        self,
        academicians: Iterable[Faculty],
        selected_record_types: set[str],
        year_scope: YearScope,
    ) -> ReportResult:
        self._validate_record_types(selected_record_types)

        result = ReportResult()

        for academician in academicians:
            self._collect_for_academician(
                academician=academician,
                selected_record_types=selected_record_types,
                year_scope=year_scope,
                result=result,
            )

        return result

    def _collect_for_academician(
        self,
        academician: Faculty,
        selected_record_types: set[str],
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
        publication_types = {
            "article",
            "conference_paper",
            "book",
        }

        activity_types = {
            "project",
            "patent",
        }

        if selected_record_types & publication_types:
            self._collect_publications(
                academician=academician,
                selected_record_types=selected_record_types,
                year_scope=year_scope,
                result=result,
            )

        if selected_record_types & activity_types:
            self._collect_activities(
                academician=academician,
                selected_record_types=selected_record_types,
                year_scope=year_scope,
                result=result,
            )

    def _collect_publications(
        self,
        academician: Faculty,
        selected_record_types: set[str],
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
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
            return

        for item in items:
            if item.record_type.value not in selected_record_types:
                continue

            try:
                detail_page = self._client.get_html(item.detail_url)
                detail = parse_detail_page(detail_page.html)

                record = normalize_publication(
                    academician_id=academician.id,
                    academician_name=academician.full_name,
                    item=item,
                    detail=detail,
                )
            except (AvesisRequestError, ValueError) as error:
                self._add_issue(
                    result=result,
                    academician=academician,
                    record_type=item.record_type.value,
                    source_url=item.detail_url,
                    message=str(error),
                )
                continue

            if record_matches_year_scope(record, year_scope):
                result.records.append(record)

    def _collect_activities(
        self,
        academician: Faculty,
        selected_record_types: set[str],
        year_scope: YearScope,
        result: ReportResult,
    ) -> None:
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
            return

        for item in items:
            if item.record_type.value not in selected_record_types:
                continue

            try:
                detail_page = self._client.get_html(item.detail_url)
                detail = parse_detail_page(detail_page.html)

                record = normalize_activity(
                    academician_id=academician.id,
                    academician_name=academician.full_name,
                    item=item,
                    detail=detail,
                )
            except (AvesisRequestError, ValueError) as error:
                self._add_issue(
                    result=result,
                    academician=academician,
                    record_type=item.record_type.value,
                    source_url=item.detail_url,
                    message=str(error),
                )
                continue

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