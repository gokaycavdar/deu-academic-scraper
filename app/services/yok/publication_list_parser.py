from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag


PUBLICATION_RECORD_TYPES = {
    "article",
    "conference_paper",
    "book",
}


@dataclass(frozen=True)
class YokPublicationListItem:
    record_type: str
    title: str
    contributor_names: str
    year: int | None
    detail_url: str | None
    data: dict[str, str | None]


def parse_publication_list(
    html: str,
    *,
    record_type: str,
    page_url: str,
) -> list[YokPublicationListItem]:
    if record_type not in PUBLICATION_RECORD_TYPES:
        raise ValueError(
            f"Desteklenmeyen YÖK yayın türü: {record_type}"
        )

    soup = BeautifulSoup(html, "html.parser")

    if record_type == "book":
        return _parse_books(soup)

    return _parse_table_publications(
        soup=soup,
        record_type=record_type,
        page_url=page_url,
    )


def _parse_table_publications(
    *,
    soup: BeautifulSoup,
    record_type: str,
    page_url: str,
) -> list[YokPublicationListItem]:
    items: list[YokPublicationListItem] = []
    seen_detail_urls: set[str] = set()

    for row in soup.select("tr"):
        detail_link = row.select_one(
            'a[data-target="#remoteModal"][href]'
        )

        if detail_link is None:
            continue

        title = _clean_text(
            detail_link.get_text(" ", strip=True)
        )

        if not title:
            continue

        content_cell = detail_link.find_parent("td")

        if content_cell is None:
            continue

        plain_text = _clean_text(
            content_cell.get_text(" ", strip=True)
        )

        venue, year = _extract_venue_and_year(plain_text)
        contributor_names = _extract_contributors(content_cell)

        data: dict[str, str | None] = {
            "venue": venue,
            "scope": _label_value(content_cell, "label-info"),
            "doi": _extract_doi(content_cell),
        }

        if record_type == "article":
            data.update(
                {
                    "peer_review": _label_value(
                        content_cell,
                        "label-primary",
                    ),
                    "index_type": _label_value(
                        content_cell,
                        "label-success",
                    ),
                    "publication_type": _label_value(
                        content_cell,
                        "label-default",
                    ),
                }
            )
        else:
            start_date, end_date = _extract_event_dates(plain_text)

            data.update(
                {
                    "index_type": _label_value(
                        content_cell,
                        "label-success",
                    ),
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

        detail_href = detail_link.get("href")

        if not isinstance(detail_href, str):
            continue

        detail_url = urljoin(page_url, detail_href)

        if detail_url in seen_detail_urls:
            continue

        seen_detail_urls.add(detail_url)

        items.append(
            YokPublicationListItem(
                record_type=record_type,
                title=title,
                contributor_names=contributor_names,
                year=year,
                detail_url=detail_url,
                data=data,
            )
        )

    return items


def _parse_books(
    soup: BeautifulSoup,
) -> list[YokPublicationListItem]:
    items: list[YokPublicationListItem] = []

    for record in soup.select(".projects > .row"):
        title_element = record.select_one(
            ".col-lg-11 strong, .col-md-10 strong"
        )

        if title_element is None:
            continue

        book_title = _remove_sequence_prefix(
            _clean_text(title_element.get_text(" ", strip=True))
        )

        if not book_title:
            continue

        metadata_element = next(
            (
                paragraph
                for paragraph in record.find_all("p")
                if "Yayın Yeri:" in paragraph.get_text(
                    " ",
                    strip=True,
                )
            ),
            None,
        )

        if metadata_element is None:
            continue

        metadata_raw = metadata_element.get_text(
            "",
            strip=False,
        )
        metadata = _clean_text(metadata_raw)

        chapter_title, chapter_contributors = (
            _extract_chapter_metadata(metadata_raw)
        )

        is_chapter = chapter_title is not None

        if is_chapter:
            title = chapter_title
            contributor_names = chapter_contributors or ""
        else:
            title = book_title
            contributor_names = _extract_book_contributors(
                metadata
            )

        items.append(
            YokPublicationListItem(
                record_type="book",
                title=title,
                contributor_names=contributor_names,
                year=_parse_year(
                    _label_value(record, "label-info")
                ),
                detail_url=None,
                data={
                    "book_title": (
                        book_title if is_chapter else None
                    ),
                    "publisher": _extract_labeled_value(
                        metadata,
                        "Yayın Yeri",
                        (
                            "Editör",
                            "Basım sayısı",
                            "Sayfa sayısı",
                            "ISBN",
                            "Bölüm Sayfaları",
                        ),
                    ),
                    "editors": _extract_labeled_value(
                        metadata,
                        "Editör",
                        (
                            "Basım sayısı",
                            "Sayfa sayısı",
                            "ISBN",
                            "Bölüm Sayfaları",
                        ),
                    ),
                    "edition": _extract_labeled_value(
                        metadata,
                        "Basım sayısı",
                        (
                            "Sayfa sayısı",
                            "ISBN",
                            "Bölüm Sayfaları",
                        ),
                    ),
                    "page_count": _extract_labeled_value(
                        metadata,
                        "Sayfa sayısı",
                        (
                            "ISBN",
                            "Bölüm Sayfaları",
                        ),
                    ),
                    "isbn": _extract_labeled_value(
                        metadata,
                        "ISBN",
                        ("Bölüm Sayfaları",),
                    ),
                    "chapter_pages": _extract_labeled_value(
                        metadata,
                        "Bölüm Sayfaları",
                        (),
                    ),
                    "publication_type": _label_value(
                        record,
                        "label-primary",
                    ),
                    "book_kind": _label_value(
                        record,
                        "label-success",
                    ),
                },
            )
        )

    return items


def _extract_chapter_metadata(
    metadata_raw: str,
) -> tuple[str | None, str | None]:
    line_break_match = re.search(
        r"Bölüm Adı\s*:\s*(?P<title>.*?)\s*,\s*"
        r"(?:\r?\n\s*)+(?P<contributors>.*?)\s*,\s*"
        r"(?:\r?\n\s*)+Yayın Yeri\s*:",
        metadata_raw,
        flags=re.DOTALL,
    )

    if line_break_match is not None:
        return (
            _clean_text(line_break_match.group("title")),
            _clean_contributor_names(
                line_break_match.group("contributors")
            ),
        )

    metadata = _clean_text(metadata_raw)

    fallback_match = re.search(
        r"Bölüm Adı\s*:\s*(?P<title>.*?)\s*,\s*"
        r"(?P<contributors>"
        r"[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]+"
        r"(?:,\s*[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]+)*"
        r")\s*,\s*Yayın Yeri\s*:",
        metadata,
    )

    if fallback_match is None:
        return None, None

    return (
        _clean_text(fallback_match.group("title")),
        _clean_contributor_names(
            fallback_match.group("contributors")
        ),
    )


def _extract_book_contributors(metadata: str) -> str:
    value = metadata.split("Yayın Yeri:", maxsplit=1)[0]
    return _clean_contributor_names(value)


def _clean_contributor_names(value: str) -> str:
    cleaned = _clean_text(value).strip(", ")
    return re.sub(r"\s*,\s*", ", ", cleaned)


def _extract_contributors(element: Tag) -> str:
    names = [
        _clean_text(link.get_text(" ", strip=True))
        for link in element.select("a.popoverData")
    ]

    return ", ".join(name for name in names if name)


def _extract_venue_and_year(
    text: str,
) -> tuple[str | None, int | None]:
    match = re.search(
        r"Yayın Yeri\s*:\s*(.*?)\s*,\s*(\d{4})(?:\s|$)",
        text,
    )

    if match is None:
        return None, _parse_year(text)

    return _clean_text(match.group(1)), int(match.group(2))


def _extract_event_dates(
    text: str,
) -> tuple[str | None, str | None]:
    match = re.search(
        r"\(\s*(\d{2}\.\d{2}\.\d{4})\s*-\s*"
        r"(\d{2}\.\d{2}\.\d{4})\s*\)",
        text,
    )

    if match is None:
        return None, None

    return match.group(1), match.group(2)


def _extract_doi(element: Tag) -> str | None:
    for link in element.select("a[href]"):
        href = link.get("href", "")

        if not isinstance(href, str):
            continue

        if "doi.org/" not in href.casefold():
            continue

        return _clean_text(link.get_text(" ", strip=True))

    return None


def _extract_labeled_value(
    text: str,
    label: str,
    next_labels: tuple[str, ...],
) -> str | None:
    next_label_pattern = "|".join(
        re.escape(next_label)
        for next_label in next_labels
    )

    if next_label_pattern:
        end_pattern = (
            rf"(?=,\s*(?:{next_label_pattern})\s*:|$)"
        )
    else:
        end_pattern = r"$"

    match = re.search(
        rf"{re.escape(label)}\s*:\s*(.*?){end_pattern}",
        text,
    )

    if match is None:
        return None

    value = _clean_text(match.group(1)).rstrip(", ")

    return value or None


def _label_value(
    element: Tag,
    class_name: str,
) -> str | None:
    label = element.select_one(f"span.{class_name}")

    if label is None:
        return None

    value = _clean_text(label.get_text(" ", strip=True))
    return value or None


def _parse_year(value: str | None) -> int | None:
    if not value:
        return None

    match = re.search(r"(?<!\d)(\d{4})(?!\d)", value)

    if match is None:
        return None

    return int(match.group(1))


def _remove_sequence_prefix(value: str) -> str:
    return re.sub(r"^\d+\.\s*", "", value).strip()


def _clean_text(value: str) -> str:
    cleaned = " ".join(value.split())
    return re.sub(r"\s+([,;])", r"\1", cleaned)