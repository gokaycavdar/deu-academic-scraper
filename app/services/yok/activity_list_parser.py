from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag


ACTIVITY_RECORD_TYPES = {
    "project",
    "patent",
}


@dataclass(frozen=True)
class YokActivityListItem:
    record_type: str
    title: str
    contributor_names: str
    year: int | None
    data: dict[str, str | None]


def parse_activity_list(
    html: str,
    *,
    record_type: str,
) -> list[YokActivityListItem]:
    if record_type not in ACTIVITY_RECORD_TYPES:
        raise ValueError(
            f"Desteklenmeyen YÖK faaliyet türü: {record_type}"
        )

    soup = BeautifulSoup(html, "html.parser")

    if record_type == "project":
        return _parse_projects(soup)

    return _parse_patents(soup)


def _parse_projects(
    soup: BeautifulSoup,
) -> list[YokActivityListItem]:
    items: list[YokActivityListItem] = []

    for record in soup.select(".projectmain"):
        title_element = record.select_one(".baslika strong")

        if title_element is None:
            continue

        title = _clean_text(
            title_element.get_text(" ", strip=True)
        )

        if not title:
            continue

        project_type_element = record.select_one(".projectType")

        project_type_text = (
            _text_without_labels(project_type_element)
            if project_type_element is not None
            else ""
        )
        start_date, end_date = _extract_date_range(
            project_type_text
        )
        budget_amount, budget_currency = _extract_budget(
            project_type_text
        )

        items.append(
            YokActivityListItem(
                record_type="project",
                title=title,
                contributor_names=_extract_contributors(record),
                year=_year_from_date(start_date),
                data={
                    "supporting_organization": _label_value(
                        record,
                        "label-default",
                    ),
                    "project_type": _label_value(
                        record,
                        "label-primary",
                    ),
                    "status": _label_value(
                        record,
                        "label-success",
                    ),
                    "start_date": start_date,
                    "end_date": end_date,
                    "start_year": _year_text(start_date),
                    "end_year": _year_text(end_date),
                    "budget_amount": budget_amount,
                    "budget_currency": budget_currency,
                },
            )
        )

    return items


def _parse_patents(
    soup: BeautifulSoup,
) -> list[YokActivityListItem]:
    items: list[YokActivityListItem] = []

    for record in soup.select(".projectmain"):
        title_element = record.select_one(".projectTitle strong")

        if title_element is None:
            continue

        raw_title = _clean_text(
            title_element.get_text(" ", strip=True)
        )

        title, registration_number = _split_patent_title(
            raw_title
        )

        if not title:
            continue

        author_element = record.select_one(".projectAuthor")
        author_text = (
            _clean_text(author_element.get_text(" ", strip=True))
            if author_element is not None
            else ""
        )
        applicants, inventors = _extract_patent_people(
            author_text
        )

        items.append(
            YokActivityListItem(
                record_type="patent",
                title=title,
                contributor_names=inventors or "",
                year=_year_from_registration_number(
                    registration_number
                ),
                data={
                    "intellectual_property": _label_value(
                        record,
                        "label-info",
                    ),
                    "patent_class": _label_value(
                        record,
                        "label-success",
                    ),
                    "registration_number": registration_number,
                    "applicants": applicants,
                    "inventors": inventors,
                },
            )
        )

    return items


def _extract_contributors(record: Tag) -> str:
    names = [
        _clean_text(link.get_text(" ", strip=True))
        for link in record.select("a.popoverData")
    ]

    return ", ".join(name for name in names if name)


def _extract_date_range(
    value: str,
) -> tuple[str | None, str | None]:
    match = re.search(
        r"(\d{2}\.\d{2}\.\d{4})\s*-\s*"
        r"(\d{2}\.\d{2}\.\d{4})",
        value,
    )

    if match is None:
        return None, None

    return match.group(1), match.group(2)


def _extract_budget(
    value: str,
) -> tuple[str | None, str | None]:
    match = re.search(
        r"\d{2}\.\d{2}\.\d{4}\s*-\s*"
        r"\d{2}\.\d{2}\.\d{4}\s*,\s*"
        r"(?P<amount>[\d.,]+)"
        r"(?:\s+(?P<currency>.+))?$",
        value,
    )

    if match is None:
        return None, None

    amount = match.group("amount").strip()
    currency = match.group("currency")

    return amount, _clean_text(currency) if currency else None


def _extract_patent_people(
    value: str,
) -> tuple[str | None, str | None]:
    applicants_match = re.search(
        r"Patent Başvuru Sahipleri\s*:\s*(.*?)"
        r"(?=\s*Patent Buluş Sahipleri\s*:|$)",
        value,
    )
    inventors_match = re.search(
        r"Patent Buluş Sahipleri\s*:\s*(.*)$",
        value,
    )

    applicants = (
        _clean_text(applicants_match.group(1))
        if applicants_match is not None
        else None
    )
    inventors = (
        _clean_contributor_names(inventors_match.group(1))
        if inventors_match is not None
        else None
    )

    return applicants or None, inventors or None


def _split_patent_title(
    value: str,
) -> tuple[str, str | None]:
    match = re.search(
        r"^(?P<title>.*?)(?:\s+(?P<number>\d{4}/\d+))?$",
        value,
    )

    if match is None:
        return value, None

    return (
        _clean_text(match.group("title")),
        match.group("number"),
    )


def _label_value(
    element: Tag,
    class_name: str,
) -> str | None:
    label = element.select_one(f"span.{class_name}")

    if label is None:
        return None

    value = _clean_text(label.get_text(" ", strip=True))
    return value or None


def _text_without_labels(element: Tag) -> str:
    clone = BeautifulSoup(str(element), "html.parser")

    for label in clone.select("span.label"):
        label.decompose()

    return _clean_text(clone.get_text(" ", strip=True)).strip(", ")


def _year_from_date(value: str | None) -> int | None:
    if value is None:
        return None

    return int(value[-4:])


def _year_text(value: str | None) -> str | None:
    year = _year_from_date(value)
    return str(year) if year is not None else None


def _year_from_registration_number(
    value: str | None,
) -> int | None:
    if value is None:
        return None

    match = re.match(r"(\d{4})/", value)

    return int(match.group(1)) if match is not None else None


def _clean_contributor_names(value: str) -> str:
    cleaned = _clean_text(value).strip(", ")
    return re.sub(r"\s*,\s*", ", ", cleaned)


def _clean_text(value: str) -> str:
    cleaned = " ".join(value.split())
    return re.sub(r"\s+([,;])", r"\1", cleaned)