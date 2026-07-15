from __future__ import annotations

import re

from bs4 import BeautifulSoup


def parse_detail_fields(html: str) -> dict[str, str]:
    """
    YÖK makale/bildiri popup HTML'indeki .te alanlarını çözer.

    Örnek sonuç:
    {
        "Adı": "...",
        "Yazar(lar)": "...",
        "Kapsam": "Uluslararası",
        "ISSN": "...",
    }
    """
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}

    for field_element in soup.select(".modal-body .te"):
        label_element = field_element.find("strong")

        if label_element is None:
            continue

        label = _clean_label(label_element.get_text(" ", strip=True))
        label_element.extract()

        value = _clean_value(
            field_element.get_text(" ", strip=True)
        )

        if not label or not value:
            continue

        previous_value = fields.get(label)

        if previous_value is not None and previous_value != value:
            raise ValueError(
                f"YÖK detayında '{label}' alanı birden fazla "
                "farklı değerle bulundu."
            )

        fields[label] = value

    if not fields:
        raise ValueError(
            "YÖK detay sayfasında alan bilgisi bulunamadı."
        )

    return fields


def _clean_label(value: str) -> str:
    return " ".join(value.split()).rstrip(":").strip()


def _clean_value(value: str) -> str:
    cleaned = " ".join(value.split())
    return re.sub(r"\s+([,;])", r"\1", cleaned)