from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.avesis.detail_parser import AvesisDetailRecord
from app.services.avesis.list_parser import (
    PublicationListItem,
    PublicationType,
)
from app.services.avesis.project_list_parser import (
    ActivityListItem,
    ActivityType,
)


@dataclass(frozen=True)
class NormalizedRecord:
    academician_id: str
    academician_name: str
    record_id: str
    record_type: str
    title: str
    contributor_names: str
    contributor_text: str
    source_url: str
    citation_text: str
    year: int | None
    data: dict[str, str | int | None]
    source_names: tuple[str, ...] = ("AVESİS",)

def normalize_publication(
    academician_id: str,
    academician_name: str,
    item: PublicationListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    if item.record_type is PublicationType.ARTICLE:
        return _normalize_article(
            academician_id,
            academician_name,
            item,
            detail,
        )

    if item.record_type is PublicationType.CONFERENCE_PAPER:
        return _normalize_conference_paper(
            academician_id,
            academician_name,
            item,
            detail,
        )

    if item.record_type is PublicationType.BOOK:
        return _normalize_book(
            academician_id,
            academician_name,
            item,
            detail,
        )

    raise ValueError(f"Desteklenmeyen yayın türü: {item.record_type}")


def normalize_activity(
    academician_id: str,
    academician_name: str,
    item: ActivityListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    if item.record_type is ActivityType.PROJECT:
        return _normalize_project(
            academician_id,
            academician_name,
            item,
            detail,
        )

    if item.record_type is ActivityType.PATENT:
        return _normalize_patent(
            academician_id,
            academician_name,
            item,
            detail,
        )

    raise ValueError(f"Desteklenmeyen aktivite türü: {item.record_type}")


def _normalize_article(
    academician_id: str,
    academician_name: str,
    item: PublicationListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    publication_date = _field(detail, "Basım Tarihi")
    pages = _field(detail, "Sayfa Sayıları")
    page_start, page_end = _split_page_range(pages)

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=item.record_id,
        record_type="article",
        detail_url=item.detail_url,
        detail=detail,
        year=_extract_year(publication_date),
        data={
            "publication_type": _field(detail, "Yayın Türü"),
            "publication_date": publication_date,
            "journal_name": _field(detail, "Dergi Adı"),
            "volume": _field(detail, "Cilt numarası"),
            "issue": _field(detail, "Sayı"),
            "pages": pages,
            "page_start": page_start,
            "page_end": page_end,
            "doi": _field(detail, "Doi Numarası"),
            "journal_indexes": _field(
                detail,
                "Derginin Tarandığı İndeksler",
            ),
            "keywords": _field(detail, "Anahtar Kelimeler"),
            "deu_addressed": _field(
                detail,
                "Dokuz Eylül Üniversitesi Adresli",
            ),
        },
    )


def _normalize_conference_paper(
    academician_id: str,
    academician_name: str,
    item: PublicationListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    city = _field(detail, "Basıldığı Şehir")
    country = _field(detail, "Basıldığı Ülke")
    conference_name = _extract_conference_name(
        detail.citation_text,
        city,
        country,
    )
    conference_date = _extract_conference_date(
        detail.citation_text,
        city,
        country,
    )
    pages = _field(detail, "Sayfa Sayıları")
    page_start, page_end = _split_page_range(pages)

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=item.record_id,
        record_type="conference_paper",
        detail_url=item.detail_url,
        detail=detail,
        year=_extract_year(conference_date or detail.citation_text),
        data={
            "publication_type": _field(detail, "Yayın Türü"),
            "conference_name": conference_name,
            "conference_date": conference_date,
            "city": city,
            "country": country,
            "pages": pages,
            "page_start": page_start,
            "page_end": page_end,
            "doi": _field(detail, "Doi Numarası"),
            "keywords": _field(detail, "Anahtar Kelimeler"),
            "deu_addressed": _field(
                detail,
                "Dokuz Eylül Üniversitesi Adresli",
            ),
        },
    )


def _normalize_book(
    academician_id: str,
    academician_name: str,
    item: PublicationListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    publication_date = _field(detail, "Basım Tarihi")
    pages = _field(detail, "Sayfa Sayıları")
    page_start, page_end = _split_page_range(pages)
    editors = _field(detail, "Editörler")

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=item.record_id,
        record_type="book",
        detail_url=item.detail_url,
        detail=detail,
        year=_extract_year(publication_date),
        data={
            "publication_type": _field(detail, "Yayın Türü"),
            "publication_date": publication_date,
            "book_title": _extract_book_title(
            citation_text=detail.citation_text,
            editors=editors,
                ),
            "publisher": _field(detail, "Yayınevi"),
            "city": _field(detail, "Basıldığı Şehir"),
            "pages": pages,
            "page_start": page_start,
            "page_end": page_end,
            "editors": editors,
            "deu_addressed": _field(
                detail,
                "Dokuz Eylül Üniversitesi Adresli",
            ),
        },
    )


def _normalize_project(
    academician_id: str,
    academician_name: str,
    item: ActivityListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    start_date = _field(detail, "Başlama Tarihi")
    end_date = _field(detail, "Bitiş Tarihi")

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=item.record_id,
        record_type="project",
        detail_url=item.detail_url,
        detail=detail,
        year=_extract_year(start_date),
        data={
            "project_type": _field(detail, "Proje Türü"),
            "support_program": _field(detail, "Destek Programı"),
            "supporting_organization": None,
            "start_date": start_date,
            "end_date": end_date,
            "start_year": _extract_year(start_date),
            "end_year": _extract_year(end_date),
        },
    )


def _normalize_patent(
    academician_id: str,
    academician_name: str,
    item: ActivityListItem,
    detail: AvesisDetailRecord,
) -> NormalizedRecord:
    application_date = _field(detail, "Başvuru Tarihi")
    registration_date = _field(detail, "Tescil Tarihi")

    return _build_record(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=item.record_id,
        record_type="patent",
        detail_url=item.detail_url,
        detail=detail,
        year=(
            _extract_year(registration_date)
            or _extract_year(application_date)
        ),
        data={
            "intellectual_property": _field(
                detail,
                "Fikri Mülkiyet",
            ),
            "application_country": _field(
                detail,
                "Başvuru Yapılan Ülke/Kuruluş",
            ),
            "status": _field(detail, "Buluşun Durumu"),
            "application_date": application_date,
            "registration_date": registration_date,
            "registration_number": _extract_registration_number(
                detail.citation_text
            ),
            "registration_type": _extract_registration_type(
                detail.citation_text
            ),
            "patent_class": _extract_patent_class(
                detail.citation_text
            ),
        },
    )


def _build_record(
    academician_id: str,
    academician_name: str,
    record_id: str,
    record_type: str,
    detail_url: str,
    detail: AvesisDetailRecord,
    year: int | None,
    data: dict[str, str | int | None],
) -> NormalizedRecord:
    contributor_names = ", ".join(detail.contributor_names)

    return NormalizedRecord(
        academician_id=academician_id,
        academician_name=academician_name,
        record_id=record_id,
        record_type=record_type,
        title=detail.title,
        contributor_names=contributor_names,
        contributor_text=_clean_text(detail.contributor_text),
        source_url=detail_url,
        citation_text=detail.citation_text,
        year=year,
        data=data,
    )


def _field(
    detail: AvesisDetailRecord,
    field_name: str,
) -> str | None:
    value = detail.fields.get(field_name)

    if value is None:
        return None

    value = _clean_text(value)
    return value or None


def _split_page_range(
    pages: str | None,
) -> tuple[str | None, str | None]:
    if pages is None:
        return None, None

    match = re.search(r"(\d+)\s*[-–]\s*(\d+)", pages)

    if match is None:
        return None, None

    return match.group(1), match.group(2)


def _extract_year(value: str | None) -> int | None:
    if not value:
        return None

    years = re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", value)

    if not years:
        return None

    return int(years[-1])


def _extract_conference_name(
    citation_text: str,
    city: str | None,
    country: str | None,
) -> str | None:
    if not citation_text:
        return None

    if city and country:
        marker = f", {city}, {country},"

        if marker in citation_text:
            return citation_text.split(marker, maxsplit=1)[0].strip()

    return citation_text


def _extract_conference_date(
    citation_text: str,
    city: str | None,
    country: str | None,
) -> str | None:
    if not citation_text or not city or not country:
        return None

    marker = f", {city}, {country},"

    if marker not in citation_text:
        return None

    remaining_text = citation_text.split(
        marker,
        maxsplit=1,
    )[1]

    date_text = remaining_text.rsplit(
        ", (",
        maxsplit=1,
    )[0].strip()

    date_text = re.sub(
        r",\s*s{1,2}\.\s*[^,]+$",
        "",
        date_text,
        flags=re.IGNORECASE,
    ).strip()

    return date_text or None


def _extract_book_title(
    citation_text: str,
    editors: str | None,
) -> str | None:
    if citation_text and editors:
        editor_names = re.sub(
            r"\s*,?\s*Editör(?:ler)?\s*$",
            "",
            editors,
            flags=re.IGNORECASE,
        ).strip(" ,")

        if editor_names:
            editor_pattern = re.escape(editor_names).replace(
                r"\ ",
                r"\s*",
            )
            match = re.search(
                rf"^(?P<book_title>.+?),\s*{editor_pattern}"
                r"\s*,\s*Editör(?:ler)?\s*,",
                citation_text,
                flags=re.IGNORECASE,
            )

            if match is not None:
                return match.group("book_title").strip() or None

    match = re.search(
        r"['“\"]([^'”\"]+)['”\"]",
        citation_text,
    )

    if match is None:
        return None

    return match.group(1).strip() or None


def _extract_registration_number(
    citation_text: str,
) -> str | None:
    match = re.search(
        r"Buluşun Tescil No:\s*([^,]+)",
        citation_text,
    )

    if match is None:
        return None

    return match.group(1).strip() or None


def _extract_registration_type(
    citation_text: str,
) -> str | None:
    match = re.search(
        r"Buluşun Tescil No:\s*[^,]+,\s*([^,]+)",
        citation_text,
    )

    if match is None:
        return None

    return match.group(1).strip() or None


def _extract_patent_class(
    citation_text: str,
) -> str | None:
    before_registration = citation_text.split(
        "Buluşun Tescil No:",
        maxsplit=1,
    )[0]

    parts = [
        part.strip()
        for part in before_registration.split(",")
        if part.strip()
    ]

    if len(parts) < 2:
        return None

    return parts[1]


def _clean_text(value: str) -> str:
    value = " ".join(value.split())
    return re.sub(r"\s+([,;])", r"\1", value)