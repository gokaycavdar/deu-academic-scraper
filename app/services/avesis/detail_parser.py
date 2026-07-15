from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag


@dataclass(frozen=True)
class AvesisDetailRecord:
    title: str
    contributor_names: tuple[str, ...]
    contributor_text: str
    citation_text: str
    fields: dict[str, str]


def parse_detail_page(html: str) -> AvesisDetailRecord:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one("div.container.bg-white.mb-xl") or soup

    title = _extract_title(content)
    contributor_names, contributor_text = _extract_contributors(content)
    citation_text = _extract_citation_text(content)
    fields = _extract_fields(content)

    return AvesisDetailRecord(
        title=title,
        contributor_names=contributor_names,
        contributor_text=contributor_text,
        citation_text=citation_text,
        fields=fields,
    )


def _extract_title(content: Tag) -> str:
    title_element = content.select_one("h1.mb-none")

    if title_element is None:
        raise ValueError("AVESİS detay sayfasında kayıt başlığı bulunamadı.")

    title = title_element.get_text(" ", strip=True)

    if not title:
        raise ValueError("AVESİS detay sayfasındaki kayıt başlığı boş.")

    return title


def _extract_contributors(content: Tag) -> tuple[tuple[str, ...], str]:
    contributor_container = None

    for paragraph in content.select("p"):
        if paragraph.select_one("a.authorsRichText") is not None:
            contributor_container = paragraph
            break

    if contributor_container is None:
        return (), ""

    names = tuple(
        anchor.get_text(" ", strip=True)
        for anchor in contributor_container.select("a.authorsRichText")
    )

    text = contributor_container.get_text(" ", strip=True)

    return names, text


def _extract_citation_text(content: Tag) -> str:
    citation_element = content.select_one("p.mb-xlg")

    if citation_element is None:
        return ""

    return citation_element.get_text(" ", strip=True)


def _extract_fields(content: Tag) -> dict[str, str]:
    fields: dict[str, str] = {}

    for item in content.select("li.list-group-item"):
        for label in item.select("strong"):
            field_name = label.get_text(" ", strip=True).rstrip(":")

            if not field_name:
                continue

            label_container = label.parent

            if not isinstance(label_container, Tag):
                continue

            value_container = label_container.find_next_sibling(
                "span",
                class_="mr-sm",
            )

            if not isinstance(value_container, Tag):
                continue

            field_value = value_container.get_text(" ", strip=True)

            if field_value:
                fields[field_name] = field_value

    return fields