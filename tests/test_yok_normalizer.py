from app.services.yok.activity_list_parser import YokActivityListItem
from app.services.yok.normalizer import (
    YOK_SOURCE_NAME,
    normalize_activity,
    normalize_publication,
)
from app.services.yok.publication_list_parser import (
    YokPublicationListItem,
)


def test_normalizes_yok_article() -> None:
    item = YokPublicationListItem(
        record_type="article",
        title="CoMAD: Drone Networks",
        contributor_names="UMUT CAN ÇABUK, GÖKHAN DALKILIÇ",
        year=2021,
        detail_url="https://example.test/popup",
        data={
            "venue": "IEEE Access",
            "scope": "Uluslararası",
            "doi": "https://dx.doi.org/10.1109/ACCESS.2021.3083549",
            "peer_review": "Hakemli",
            "index_type": "SCI-Expanded",
            "publication_type": "Özgün Makale",
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
        {
            "ISSN": "2169-3536",
            "Anahtar kelime(ler)": "authentication, security",
        },
    )

    assert record.record_type == "article"
    assert record.year == 2021
    assert record.source_names == (YOK_SOURCE_NAME,)
    assert record.source_url == ""
    assert record.data["journal_name"] == "IEEE Access"
    assert record.data["doi"] == "10.1109/ACCESS.2021.3083549"
    assert record.data["journal_indexes"] == "SCI-Expanded"
    assert record.data["scope"] == "Uluslararası"
    assert record.data["peer_review"] == "Hakemli"
    assert record.data["issn"] == "2169-3536"


def test_normalizes_yok_conference_paper() -> None:
    item = YokPublicationListItem(
        record_type="conference_paper",
        title="Secure IoT Communication",
        contributor_names="GÖKHAN DALKILIÇ",
        year=2025,
        detail_url="https://example.test/popup",
        data={
            "venue": "ISAS 2025",
            "scope": "Uluslararası",
            "doi": None,
            "index_type": "Tam metin bildiri",
            "start_date": "27.06.2025",
            "end_date": "28.06.2025",
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
    )

    assert record.record_type == "conference_paper"
    assert record.year == 2025
    assert record.data["conference_name"] == "ISAS 2025"
    assert record.data["conference_date"] == (
        "27.06.2025 - 28.06.2025"
    )
    assert record.data["scope"] == "Uluslararası"


def test_normalizes_yok_book_chapter() -> None:
    item = YokPublicationListItem(
        record_type="book",
        title="Nesnelerin İnterneti için Sayı Üreteci",
        contributor_names="AYDIN ÖMER, DALKILIÇ GÖKHAN",
        year=2016,
        detail_url=None,
        data={
            "book_title": "Akıllı Teknoloji ve Akıllı Yönetim",
            "publisher": "Gülermat Matbaacılık",
            "editors": "TECİM Vahap, TARHAN Çiğdem",
            "edition": "1",
            "page_count": None,
            "isbn": "9786056004759",
            "chapter_pages": "121 -129",
            "publication_type": "Bilimsel Kitap",
            "book_kind": "Kitap Bölümü",
        },
    )

    record = normalize_publication(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
    )

    assert record.record_type == "book"
    assert record.data["book_title"] == (
        "Akıllı Teknoloji ve Akıllı Yönetim"
    )
    assert record.data["pages"] == "ss.121-129"
    assert record.data["page_start"] == "121"
    assert record.data["page_end"] == "129"
    assert record.data["isbn"] == "9786056004759"


def test_normalizes_yok_project() -> None:
    item = YokActivityListItem(
        record_type="project",
        title="Denetleme Kontrol Yönetimi",
        contributor_names=(
            "MEHMET HİLAL ÖZCANHAN, GÖKHAN DALKILIÇ"
        ),
        year=2013,
        data={
            "supporting_organization": "DOKUZ EYLÜL ÜNİVERSİTESİ",
            "project_type": "TÜBİTAK PROJESİ",
            "status": "Tamamlandı",
            "start_date": "01.03.2013",
            "end_date": "31.07.2014",
            "start_year": "2013",
            "end_year": "2014",
            "budget_amount": "498000",
            "budget_currency": "TÜRK LİRASI",
        },
    )

    record = normalize_activity(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
    )

    assert record.record_type == "project"
    assert record.data["supporting_organization"] == (
        "DOKUZ EYLÜL ÜNİVERSİTESİ"
    )
    assert record.data["status"] == "Tamamlandı"
    assert record.data["budget_amount"] == "498000"
    assert record.data["start_year"] == 2013
    assert record.data["end_year"] == 2014


def test_normalizes_yok_patent() -> None:
    item = YokActivityListItem(
        record_type="patent",
        title="HIZLI VE HAFİF BİR RASTSAL SAYI ÜRETECİ",
        contributor_names=(
            "Ömer Aydın, Umut Can Çabuk, Gökhan Dalkılıç"
        ),
        year=2018,
        data={
            "intellectual_property": "Patent",
            "patent_class": "SECTION G - PHYSICS",
            "registration_number": "2018/05933",
            "applicants": "Dokuz Eylül Üniversitesi",
            "inventors": (
                "Ömer Aydın, Umut Can Çabuk, Gökhan Dalkılıç"
            ),
        },
    )

    record = normalize_activity(
        "gokhan-dalkilic",
        "Gökhan Dalkılıç",
        item,
    )

    assert record.record_type == "patent"
    assert record.data["registration_number"] == "2018/05933"
    assert record.data["applicants"] == "Dokuz Eylül Üniversitesi"
    assert record.data["patent_class"] == "SECTION G - PHYSICS"