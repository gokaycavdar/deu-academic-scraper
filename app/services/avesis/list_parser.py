from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse
from uuid import UUID

from bs4 import BeautifulSoup


AVESIS_BASE_URL = "https://avesis.deu.edu.tr"

YEAR_PATTERN = re.compile(
    r"(?<!\d)(?:19|20)\d{2}(?!\d)"
)


class PublicationType(str, Enum):
    ARTICLE = "article"
    CONFERENCE_PAPER = "conference_paper"
    BOOK = "book"


@dataclass(frozen=True)
class PublicationListItem:
    record_id: str
    record_type: PublicationType
    title: str
    detail_url: str
    citation_text: str
    year: int | None


def parse_publication_list(html: str) -> list[PublicationListItem]:
    soup = BeautifulSoup(html, "html.parser")
    publications: list[PublicationListItem] = []
    seen_detail_urls: set[str] = set()

    for section in soup.select("div.ac-item"):
        section_title = _get_section_title(section)

        if section_title is None:
            continue

        record_type = _map_section_to_publication_type(
            section_title
        )

        if record_type is None:
            continue

        for publication_element in section.select(
            "div.pub-item.with-icon"
        ):
            item = _parse_publication_item(
                publication_element,
                record_type,
            )

            if item is None:
                continue

            if item.detail_url in seen_detail_urls:
                continue

            seen_detail_urls.add(item.detail_url)
            publications.append(item)

    return publications


def _get_section_title(section) -> str | None:
    header = section.select_one("div.item-head > span")

    if header is None:
        return None

    return header.get_text(" ", strip=True)


def _map_section_to_publication_type(
    section_title: str,
) -> PublicationType | None:
    normalized_title = section_title.casefold()

    if normalized_title == "makaleler":
        return PublicationType.ARTICLE

    if "bildiri" in normalized_title:
        return PublicationType.CONFERENCE_PAPER

    if normalized_title == "kitaplar":
        return PublicationType.BOOK

    return None


def _parse_publication_item(
    publication_element,
    record_type: PublicationType,
) -> PublicationListItem | None:
    anchor = publication_element.select_one(
        'h3.title a[href^="/yayin/"]'
    )

    if anchor is None:
        return None

    title_element = anchor.find("strong")
    title = (
        title_element.get_text(" ", strip=True)
        if title_element is not None
        else anchor.get_text(" ", strip=True)
    )

    citation_text = _extract_citation_text(publication_element)
    detail_url = urljoin(AVESIS_BASE_URL, anchor["href"])
    record_id = _extract_record_id(detail_url)

    return PublicationListItem(
        record_id=record_id,
        record_type=record_type,
        title=title,
        detail_url=detail_url,
        citation_text=citation_text,
        year=_extract_year(citation_text),
    )


def _extract_citation_text(publication_element) -> str:
    citation_elements = publication_element.select(
        "div.description > div.citation"
    )

    if len(citation_elements) < 2:
        return ""

    return citation_elements[1].get_text(
        " ",
        strip=True,
    )


def _extract_year(citation_text: str) -> int | None:
    matches = YEAR_PATTERN.findall(citation_text)

    if not matches:
        return None

    return int(matches[-1])


def _extract_record_id(detail_url: str) -> str:
    path_parts = urlparse(detail_url).path.strip("/").split("/")

    if len(path_parts) < 2 or path_parts[0] != "yayin":
        raise ValueError(
            f"Geçersiz yayın detay bağlantısı: {detail_url}"
        )

    record_id = path_parts[1]

    try:
        UUID(record_id)
    except ValueError as error:
        raise ValueError(
            "Yayın bağlantısında geçersiz kayıt ID'si var: "
            f"{detail_url}"
        ) from error

    return record_id