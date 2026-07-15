from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse
from uuid import UUID

from bs4 import BeautifulSoup


AVESIS_BASE_URL = "https://avesis.deu.edu.tr"


class ActivityType(str, Enum):
    PROJECT = "project"
    PATENT = "patent"


@dataclass(frozen=True)
class ActivityListItem:
    record_id: str
    record_type: ActivityType
    title: str
    detail_url: str
    list_period: str | None


def parse_project_list(html: str) -> list[ActivityListItem]:
    soup = BeautifulSoup(html, "html.parser")
    activities: list[ActivityListItem] = []

    for section in soup.select("div.ac-item"):
        section_title = _get_section_title(section)

        if section_title is None:
            continue

        record_type = _map_section_to_activity_type(section_title)

        if record_type is None:
            continue

        activities.extend(
            _parse_activity_section(section, record_type)
        )

    return activities


def _get_section_title(section) -> str | None:
    header = section.select_one("div.item-head > span")

    if header is None:
        return None

    return header.get_text(" ", strip=True)


def _map_section_to_activity_type(
    section_title: str,
) -> ActivityType | None:
    normalized_title = section_title.casefold()

    if normalized_title == "desteklenen projeler":
        return ActivityType.PROJECT

    if normalized_title == "patent":
        return ActivityType.PATENT

    return None


def _parse_activity_section(
    section,
    record_type: ActivityType,
) -> list[ActivityListItem]:
    route_prefix = (
        "/proje/"
        if record_type is ActivityType.PROJECT
        else "/fikrimulkiyet/"
    )

    activities: list[ActivityListItem] = []

    for anchor in section.select(f'a[href^="{route_prefix}"]'):
        title = anchor.get_text(" ", strip=True)

        if not title:
            continue

        detail_url = urljoin(AVESIS_BASE_URL, anchor["href"])
        record_id = _extract_record_id(detail_url, route_prefix)

        title_container = anchor.find_parent("h3")
        period_element = (
            title_container.select_one("span.shaded-label")
            if title_container is not None
            else None
        )

        list_period = (
            period_element.get_text(" ", strip=True)
            if period_element is not None
            else None
        )

        activities.append(
            ActivityListItem(
                record_id=record_id,
                record_type=record_type,
                title=title,
                detail_url=detail_url,
                list_period=list_period,
            )
        )

    return activities


def _extract_record_id(
    detail_url: str,
    route_prefix: str,
) -> str:
    path_parts = urlparse(detail_url).path.strip("/").split("/")
    expected_route = route_prefix.strip("/")

    if len(path_parts) < 2 or path_parts[0] != expected_route:
        raise ValueError(
            f"Geçersiz aktivite detay bağlantısı: {detail_url}"
        )

    record_id = path_parts[1]

    try:
        UUID(record_id)
    except ValueError as error:
        raise ValueError(
            f"Aktivite bağlantısında geçersiz kayıt ID'si var: {detail_url}"
        ) from error

    return record_id