from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
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
    records: list[NormalizedRecord] = field(
        default_factory=list
    )
    issues: list[YokCollectionIssue] = field(
        default_factory=list
    )


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
                source_url=(
                    "https://akademik.yok.gov.tr/"
                    "AkademikArama/"
                ),
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
        seen_conference_fingerprints: dict[
            tuple[str, int, str, str],
            int,
        ] = {}

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

            normalized_doi = _normalized_doi(
                record.data.get("doi")
            )

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
                fingerprint = _conference_duplicate_fingerprint(
                    record
                )

                if fingerprint is None:
                    result.records.append(record)
                else:
                    existing_index = (
                        seen_conference_fingerprints.get(fingerprint)
                    )

                    if existing_index is None:
                        seen_conference_fingerprints[fingerprint] = (
                            len(result.records)
                        )
                        result.records.append(record)
                    else:
                        result.records[existing_index] = (
                            _merge_duplicate_conference_records(
                                result.records[existing_index],
                                record,
                            )
                        )

            self._notify_progress(
                progress_callback,
                completed=completed,
                total=total,
                message=(
                    f"{academician.full_name}: "
                    f"YÖK Akademik {completed}/{total} "
                    "kayıt işlendi."
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


def _conference_duplicate_fingerprint(
    record: NormalizedRecord,
) -> tuple[str, int, str, str] | None:
    """
    Yalnızca DOI'si olmayan YÖK bildirilerindeki açık tekrar
    adaylarını belirler.

    Aynı başlık, yıl, başlangıç ve bitiş tarihine sahip kayıtlar
    tek bir bildiri kabul edilir.
    """
    if record.record_type != "conference_paper":
        return None

    if _normalized_doi(record.data.get("doi")) is not None:
        return None

    if record.year is None:
        return None

    conference_date = record.data.get("conference_date")

    if not isinstance(conference_date, str):
        return None

    date_parts = [
        part.strip()
        for part in conference_date.split(" - ", maxsplit=1)
    ]

    if len(date_parts) != 2 or not all(date_parts):
        return None

    title_key = _canonical_text(record.title)

    if not title_key:
        return None

    return (
        title_key,
        record.year,
        date_parts[0],
        date_parts[1],
    )


def _merge_duplicate_conference_records(
    first: NormalizedRecord,
    second: NormalizedRecord,
) -> NormalizedRecord:
    """
    Aynı YÖK bildirisi olduğuna karar verilen iki kayıttan daha
    dolu olanı korur; diğerinin boş alanlarını ekler.
    """
    if _record_richness(second) > _record_richness(first):
        primary = second
        secondary = first
    else:
        primary = first
        secondary = second

    merged_data = dict(primary.data)

    for field_name, secondary_value in secondary.data.items():
        primary_value = merged_data.get(field_name)

        if (
            _is_blank(primary_value)
            and not _is_blank(secondary_value)
        ):
            merged_data[field_name] = secondary_value

    source_names = tuple(
        dict.fromkeys(
            (*primary.source_names, *secondary.source_names)
        )
    )

    return replace(
        primary,
        contributor_names=(
            primary.contributor_names
            or secondary.contributor_names
        ),
        contributor_text=(
            primary.contributor_text
            or secondary.contributor_text
        ),
        citation_text=(
            primary.citation_text
            or secondary.citation_text
        ),
        source_url=primary.source_url or secondary.source_url,
        year=primary.year or secondary.year,
        data=merged_data,
        source_names=source_names,
    )


def _record_richness(
    record: NormalizedRecord,
) -> tuple[int, int]:
    populated_field_count = sum(
        not _is_blank(value)
        for value in record.data.values()
    )

    contributor_length = len(
        _canonical_text(record.contributor_names)
    )

    return populated_field_count, contributor_length


def _normalized_doi(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        value.strip(),
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"^doi\s*:\s*",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    return normalized.casefold() or None


def _canonical_text(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )
    normalized = normalized.replace("ı", "i")
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    return " ".join(
        re.findall(r"[a-z0-9]+", normalized)
    )


def _is_blank(value: object) -> bool:
    return value is None or (
        isinstance(value, str) and not value.strip()
    )