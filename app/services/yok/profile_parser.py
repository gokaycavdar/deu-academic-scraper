from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.yok.client import YOK_BASE_URL


SECTION_LABELS = {
    "Kitaplar": "book",
    "Makaleler": "article",
    "Bildiriler": "conference_paper",
    "Projeler": "project",
    "Patentler": "patent",
}

SECTION_ENDPOINTS = {
    "book": "AkademisyenYayinBilgileri",
    "article": "AkademisyenYayinBilgileri",
    "conference_paper": "AkademisyenYayinBilgileri",
    "project": "AkademisyenProjeBilgileri",
    "patent": "AkademisyenPatentBilgileri",
}


def parse_profile_sections(html: str) -> dict[str, str]:
    """
    Akademisyen profilindeki gerçek tür menülerini döndürür.

    Sonuç örneği:
    {
        "article": "https://.../AkademisyenYayinBilgileri?...",
        "project": "https://.../AkademisyenProjeBilgileri?...",
    }
    """
    soup = BeautifulSoup(html, "html.parser")
    sections: dict[str, str] = {}

    for link in soup.select("a[href]"):
        label = _clean_text(link.get_text(" ", strip=True))
        record_type = SECTION_LABELS.get(label)

        if record_type is None:
            continue

        href = link.get("href")

        if not isinstance(href, str) or not href.strip():
            continue

        expected_endpoint = SECTION_ENDPOINTS[record_type]

        if expected_endpoint not in href:
            continue

        detail_url = urljoin(f"{YOK_BASE_URL}/", href)

        previous_url = sections.get(record_type)

        if previous_url is not None and previous_url != detail_url:
            raise ValueError(
                f"YÖK profilinde '{label}' için birden fazla "
                "farklı bağlantı bulundu."
            )

        sections[record_type] = detail_url

    missing_types = set(SECTION_LABELS.values()) - set(sections)

    if missing_types:
        missing_labels = [
            label
            for label, record_type in SECTION_LABELS.items()
            if record_type in missing_types
        ]
        raise ValueError(
            "YÖK profilinde eksik kayıt türü menüleri var: "
            f"{', '.join(missing_labels)}"
        )

    return sections


def _clean_text(value: str) -> str:
    return " ".join(value.split())