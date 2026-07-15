from app.services.avesis.detail_parser import AvesisDetailRecord
from app.services.avesis.list_parser import (
    PublicationListItem,
    PublicationType,
)
from app.services.avesis.normalizer import normalize_publication


def make_item(
    record_type: PublicationType,
    title: str,
) -> PublicationListItem:
    return PublicationListItem(
        record_id=f"{record_type.value}-test",
        record_type=record_type,
        title=title,
        detail_url="https://avesis.deu.edu.tr/yayin/test",
        citation_text="",
        year=None,
    )


def test_normalizes_article_fields() -> None:
    item = make_item(
        PublicationType.ARTICLE,
        "Introducing AES and ECDSA to BLE Communication",
    )

    detail = AvesisDetailRecord(
        title=item.title,
        contributor_names=(
            "ŞEKER Ö.",
            "Çabuk U. C.",
            "DALKILIÇ G.",
        ),
        contributor_text="ŞEKER Ö., Çabuk U. C., DALKILIÇ G.",
        citation_text=(
            "IEEE Wireless Communications Letters, "
            "cilt.15, ss.765-769, 2026 (SCI-Expanded, Scopus)"
        ),
        fields={
            "Yayın Türü": "Makale / Tam Makale",
            "Cilt numarası": "15",
            "Basım Tarihi": "2026",
            "Doi Numarası": "10.1109/lwc.2025.3643497",
            "Dergi Adı": "IEEE Wireless Communications Letters",
            "Derginin Tarandığı İndeksler": (
                "Science Citation Index Expanded (SCI-EXPANDED), "
                "Scopus"
            ),
            "Sayfa Sayıları": "ss.765-769",
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
        detail,
    )

    assert record.record_type == "article"
    assert record.year == 2026
    assert record.data["journal_name"] == (
        "IEEE Wireless Communications Letters"
    )
    assert record.data["volume"] == "15"
    assert record.data["doi"] == "10.1109/lwc.2025.3643497"
    assert record.data["page_start"] == "765"
    assert record.data["page_end"] == "769"


def test_normalizes_book_chapter_parent_book_title() -> None:
    item = make_item(
        PublicationType.BOOK,
        (
            "Nesnelerin İnterneti için Sözderastsal Sayı Üreteci: "
            "Birleştirilmiş Doğrusal Geri Beslemeli Öteleyici Saklayıcı"
        ),
    )

    detail = AvesisDetailRecord(
        title=item.title,
        contributor_names=("Aydın Ö.", "Dalkılıç G."),
        contributor_text="Aydın Ö., Dalkılıç G.",
        citation_text=(
            "Akıllı Teknoloji ve Akıllı Yönetim, "
            "TECİM Vahap,TARHAN Çiğdem,AYDIN Can, Editör, "
            "Gülermat Matbaacılık, İzmir, ss.121-129, 2016"
        ),
        fields={
            "Yayın Türü": "Kitapta Bölüm / Mesleki Kitap",
            "Basım Tarihi": "2016",
            "Yayınevi": "Gülermat Matbaacılık",
            "Basıldığı Şehir": "İzmir",
            "Sayfa Sayıları": "ss.121-129",
            "Editörler": (
                "TECİM Vahap,TARHAN Çiğdem,AYDIN Can, Editör"
            ),
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
        detail,
    )

    assert record.record_type == "book"
    assert record.year == 2016
    assert record.data["book_title"] == (
        "Akıllı Teknoloji ve Akıllı Yönetim"
    )
    assert record.data["page_start"] == "121"
    assert record.data["page_end"] == "129"


def test_normalizes_conference_name_and_date() -> None:
    item = make_item(
        PublicationType.CONFERENCE_PAPER,
        "On the Fundamental Limitations of Neural Networks",
    )

    detail = AvesisDetailRecord(
        title=item.title,
        contributor_names=("DURMUŞ O.", "DALKILIÇ G."),
        contributor_text="DURMUŞ O., DALKILIÇ G.",
        citation_text=(
            "2026 8th International Congress on Human-Computer "
            "Interaction, Optimization and Robotic Applications "
            "(ICHORA), Ankara, Türkiye, 21 Mayıs 2026, "
            "(Tam Metin Bildiri)"
        ),
        fields={
            "Yayın Türü": "Bildiri / Tam Metin Bildiri",
            "Doi Numarası": "10.1109/ichora69329.2026.11537074",
            "Basıldığı Şehir": "Ankara",
            "Basıldığı Ülke": "Türkiye",
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
        detail,
    )

    assert record.record_type == "conference_paper"
    assert record.year == 2026
    assert record.data["conference_name"] == (
        "2026 8th International Congress on Human-Computer "
        "Interaction, Optimization and Robotic Applications (ICHORA)"
    )
    assert record.data["conference_date"] == "21 Mayıs 2026"