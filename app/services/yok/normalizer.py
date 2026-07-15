from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping

from app.services.avesis.normalizer import NormalizedRecord
from app.services.yok.activity_list_parser import YokActivityListItem
from app.services.yok.publication_list_parser import YokPublicationListItem


YOK_SOURCE_NAME = "YÖK Akademik"


def normalize_publication(
    academician_id: str,
    academician_name: str,
    item: YokPublicationListItem,
    detail_fields: Mapping[str, str] | None = None,
) -> NormalizedRecord:
    detail = detail_fields or {}

    if item.record_type == "article":
        return _normalize_article(
            academician_id,
            academician_name,
            item,
            detail,
        )

    if item.record_type == "conference_paper":
        return _normalize_conference_paper(
            academician_id,
            academician_name,
            item,
            detail,
        )

    if item.record_type == "book":
        return _normalize_book(
            academician_id,
            academician_name,
            item,
        )

    raise ValueError(
        f"Desteklenmeyen YÖK yayın türü: {item.record_type}"
    )


def normalize_activity(
    academician_id: str,
    academician_name: str,
    item: YokActivityListItem,
) -> NormalizedRecord:
    if item.record_type == "project":
        return _normalize_project(
            academician_id,
            academician_name,
            item,
        )

    if item.record_type == "patent":
        return _normalize_patent(
            academician_id,
            academician_name,
            item,
        )

    raise ValueError(
        f"Desteklenmeyen YÖK faaliyet türü: {item.record_type}"
    )


def _normalize_article(
    academician_id: str,
    academician_name: str,
    item: YokPublicationListItem,
    detail: Mapping[str, str],
) -> NormalizedRecord:
    venue = _pick(
        _detail_value(detail, "Yayın Yeri"),
        _data_value(item.data, "venue"),
    )
    publication_date = _pick(
        _detail_value(detail, "Yıl"),
        str(item.year) if item.year is not None else None,
    )
    doi = _normalize_doi(
        _pick(
            _detail_value(detail, "DOI"),
            _data_value(item.data, "doi"),
        )
    )

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_type="article",
        title=item.title,
        contributor_names=item.contributor_names,
        year=_extract_year(publication_date) or item.year,
        citation_text=_citation_text(venue, publication_date),
        data={
            "publication_type": _pick(
                _detail_value(detail, "Tür"),
                _data_value(item.data, "publication_type"),
            ),
            "publication_date": publication_date,
            "journal_name": venue,
            "volume": None,
            "issue": None,
            "pages": None,
            "page_start": None,
            "page_end": None,
            "doi": doi,
            "journal_indexes": _pick(
                _detail_value(detail, "İndeks türü"),
                _data_value(item.data, "index_type"),
            ),
            "keywords": _detail_value(
                detail,
                "Anahtar kelime(ler)",
            ),
            "deu_addressed": None,
            "scope": _pick(
                _detail_value(detail, "Kapsam"),
                _data_value(item.data, "scope"),
            ),
            "peer_review": _pick(
                _detail_value(detail, "Hakem"),
                _data_value(item.data, "peer_review"),
            ),
            "issn": _detail_value(detail, "ISSN"),
        },
    )


def _normalize_conference_paper(
    academician_id: str,
    academician_name: str,
    item: YokPublicationListItem,
    detail: Mapping[str, str],
) -> NormalizedRecord:
    conference_name = _pick(
        _detail_value(detail, "Yayın Yeri"),
        _data_value(item.data, "venue"),
    )
    start_date = _pick(
        _detail_value(detail, "Başlama tarihi"),
        _data_value(item.data, "start_date"),
    )
    end_date = _pick(
        _detail_value(detail, "Bitiş tarihi"),
        _data_value(item.data, "end_date"),
    )
    conference_date = _format_date_range(start_date, end_date)
    doi = _normalize_doi(
        _pick(
            _detail_value(detail, "DOI"),
            _data_value(item.data, "doi"),
        )
    )

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_type="conference_paper",
        title=item.title,
        contributor_names=item.contributor_names,
        year=_extract_year(
            _pick(
                _detail_value(detail, "Yıl"),
                conference_date,
            )
        )
        or item.year,
        citation_text=_citation_text(
            conference_name,
            conference_date or (
                str(item.year) if item.year is not None else None
            ),
        ),
        data={
            "publication_type": _pick(
                _detail_value(detail, "Tür"),
                _data_value(item.data, "index_type"),
            ),
            "conference_name": conference_name,
            "conference_date": conference_date,
            "city": None,
            "country": None,
            "pages": None,
            "page_start": None,
            "page_end": None,
            "doi": doi,
            "keywords": _detail_value(
                detail,
                "Anahtar kelime(ler)",
            ),
            "deu_addressed": None,
            "scope": _pick(
                _detail_value(detail, "Kapsam"),
                _data_value(item.data, "scope"),
            ),
        },
    )


def _normalize_book(
    academician_id: str,
    academician_name: str,
    item: YokPublicationListItem,
) -> NormalizedRecord:
    pages = _normalize_pages(
        _data_value(item.data, "chapter_pages")
    )
    page_start, page_end = _split_page_range(pages)
    publication_type = _combine_book_type(
        _data_value(item.data, "book_kind"),
        _data_value(item.data, "publication_type"),
    )

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_type="book",
        title=item.title,
        contributor_names=item.contributor_names,
        year=item.year,
        citation_text=_citation_text(
            _data_value(item.data, "publisher"),
            str(item.year) if item.year is not None else None,
        ),
        data={
            "publication_type": publication_type,
            "publication_date": (
                str(item.year) if item.year is not None else None
            ),
            "book_title": _data_value(item.data, "book_title"),
            "publisher": _data_value(item.data, "publisher"),
            "city": None,
            "pages": pages,
            "page_start": page_start,
            "page_end": page_end,
            "editors": _data_value(item.data, "editors"),
            "deu_addressed": None,
            "isbn": _data_value(item.data, "isbn"),
            "edition": _data_value(item.data, "edition"),
            "page_count": _data_value(item.data, "page_count"),
        },
    )


def _normalize_project(
    academician_id: str,
    academician_name: str,
    item: YokActivityListItem,
) -> NormalizedRecord:
    start_date = _data_value(item.data, "start_date")
    end_date = _data_value(item.data, "end_date")

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_type="project",
        title=item.title,
        contributor_names=item.contributor_names,
        year=item.year or _extract_year(start_date),
        citation_text=_citation_text(
            _data_value(item.data, "project_type"),
            _format_date_range(start_date, end_date),
        ),
        data={
            "project_type": _data_value(
                item.data,
                "project_type",
            ),
            "support_program": None,
            "supporting_organization": _data_value(
                item.data,
                "supporting_organization",
            ),
            "start_date": start_date,
            "end_date": end_date,
            "start_year": _extract_year(start_date),
            "end_year": _extract_year(end_date),
            "status": _data_value(item.data, "status"),
            "budget_amount": _data_value(
                item.data,
                "budget_amount",
            ),
            "budget_currency": _data_value(
                item.data,
                "budget_currency",
            ),
        },
    )


def _normalize_patent(
    academician_id: str,
    academician_name: str,
    item: YokActivityListItem,
) -> NormalizedRecord:
    registration_number = _data_value(
        item.data,
        "registration_number",
    )

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_type="patent",
        title=item.title,
        contributor_names=item.contributor_names,
        year=item.year,
        citation_text=_citation_text(
            _data_value(item.data, "patent_class"),
            registration_number,
        ),
        data={
            "intellectual_property": _data_value(
                item.data,
                "intellectual_property",
            ),
            "application_country": None,
            "status": None,
            "application_date": None,
            "registration_date": None,
            "registration_number": registration_number,
            "registration_type": None,
            "patent_class": _data_value(
                item.data,
                "patent_class",
            ),
            "applicants": _data_value(item.data, "applicants"),
        },
    )


def _build_record(
    *,
    academician_id: str,
    academician_name: str,
    record_type: str,
    title: str,
    contributor_names: str,
    year: int | None,
    citation_text: str,
    data: dict[str, str | int | None],
) -> NormalizedRecord:
    clean_title = _clean_text(title)
    clean_contributors = _clean_text(contributor_names)

    return NormalizedRecord(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=_build_record_id(
            record_type,
            clean_title,
            year,
            clean_contributors,
        ),
        record_type=record_type,
        title=clean_title,
        contributor_names=clean_contributors,
        contributor_text=clean_contributors,
        # YÖK popup URL'leri oturuma bağlıdır; Excel'e kalıcı link
        # olarak yazılmamalıdır.
        source_url="",
        citation_text=citation_text,
        year=year,
        data=data,
        source_names=(YOK_SOURCE_NAME,),
    )


def _build_record_id(
    record_type: str,
    title: str,
    year: int | None,
    contributor_names: str,
) -> str:
    payload = "\x1f".join(
        (
            record_type,
            title.casefold(),
            str(year or ""),
            contributor_names.casefold(),
        )
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]

    return f"yok-{record_type}-{digest}"


def _detail_value(
    detail: Mapping[str, str],
    field_name: str,
) -> str | None:
    return _clean_optional(detail.get(field_name))


def _data_value(
    data: Mapping[str, str | None],
    field_name: str,
) -> str | None:
    return _clean_optional(data.get(field_name))


def _pick(*values: str | None) -> str | None:
    for value in values:
        cleaned = _clean_optional(value)

        if cleaned:
            return cleaned

    return None


def _normalize_doi(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        value,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"^doi\s*:\s*",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    return normalized.strip() or None


def _format_date_range(
    start_date: str | None,
    end_date: str | None,
) -> str | None:
    if start_date and end_date:
        if start_date == end_date:
            return start_date

        return f"{start_date} - {end_date}"

    return start_date or end_date


def _normalize_pages(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = re.sub(r"\s*-\s*", "-", value.strip())

    if not normalized:
        return None

    if normalized.casefold().startswith("ss."):
        return normalized

    return f"ss.{normalized}"


def _split_page_range(
    pages: str | None,
) -> tuple[str | None, str | None]:
    if pages is None:
        return None, None

    match = re.search(r"(\d+)\s*[-–]\s*(\d+)", pages)

    if match is None:
        return None, None

    return match.group(1), match.group(2)


def _combine_book_type(
    book_kind: str | None,
    publication_type: str | None,
) -> str | None:
    values = [
        value
        for value in (book_kind, publication_type)
        if value
    ]

    return " / ".join(values) or None


def _citation_text(
    first_value: str | None,
    second_value: str | None,
) -> str:
    return ", ".join(
        value
        for value in (first_value, second_value)
        if value
    )


def _extract_year(value: str | None) -> int | None:
    if not value:
        return None

    match = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", value)

    return int(match.group(1)) if match is not None else None


def _clean_optional(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    cleaned = _clean_text(value)
    return cleaned or None


def _clean_text(value: str) -> str:
    cleaned = " ".join(value.split())
    return re.sub(r"\s+([,;])", r"\1", cleaned)