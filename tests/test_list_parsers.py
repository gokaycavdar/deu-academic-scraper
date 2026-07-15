from app.services.avesis.list_parser import (
    PublicationType,
    parse_publication_list,
)
from app.services.avesis.project_list_parser import (
    ActivityType,
    parse_project_list,
)


def test_parses_publication_sections_and_detail_urls() -> None:
    html = """
    <div class="ac-item">
        <div class="item-head"><span>Makaleler</span></div>
        <div class="pub-item with-icon">
            <h3 class="title">
                <a href="/yayin/11111111-1111-4111-8111-111111111111/article">
                    <strong>Makale Başlığı</strong>
                </a>
            </h3>
        </div>
    </div>

    <div class="ac-item">
        <div class="item-head"><span>Bildiriler</span></div>
        <div class="pub-item with-icon">
            <h3 class="title">
                <a href="/yayin/22222222-2222-4222-8222-222222222222/paper">
                    <strong>Bildiri Başlığı</strong>
                </a>
            </h3>
        </div>
    </div>

    <div class="ac-item">
        <div class="item-head"><span>Kitaplar</span></div>
        <div class="pub-item with-icon">
            <h3 class="title">
                <a href="/yayin/33333333-3333-4333-8333-333333333333/book">
                    <strong>Kitap Başlığı</strong>
                </a>
            </h3>
        </div>
    </div>
    """

    items = parse_publication_list(html)

    assert [
        item.record_type
        for item in items
    ] == [
        PublicationType.ARTICLE,
        PublicationType.CONFERENCE_PAPER,
        PublicationType.BOOK,
    ]

    assert items[0].title == "Makale Başlığı"
    assert items[1].detail_url == (
        "https://avesis.deu.edu.tr/"
        "yayin/22222222-2222-4222-8222-222222222222/paper"
    )


def test_parses_project_and_patent_sections() -> None:
    html = """
    <div class="ac-item">
        <div class="item-head"><span>Desteklenen Projeler</span></div>
        <h3>
            <a href="/proje/44444444-4444-4444-8444-444444444444/project">
                Proje Başlığı
            </a>
            <span class="shaded-label">2024 - 2025</span>
        </h3>
    </div>

    <div class="ac-item">
        <div class="item-head"><span>Patent</span></div>
        <h3>
            <a href="/fikrimulkiyet/55555555-5555-4555-8555-555555555555/patent">
                Patent Başlığı
            </a>
        </h3>
    </div>
    """

    items = parse_project_list(html)

    assert [
        item.record_type
        for item in items
    ] == [
        ActivityType.PROJECT,
        ActivityType.PATENT,
    ]

    assert items[0].title == "Proje Başlığı"
    assert items[0].list_period == "2024 - 2025"
    assert items[1].detail_url == (
        "https://avesis.deu.edu.tr/"
        "fikrimulkiyet/55555555-5555-4555-8555-555555555555/patent"
    )
    
def test_extracts_publication_citation_and_year() -> None:
    html = """
    <div class="ac-item">
        <div class="item-head"><span>Makaleler</span></div>

        <div class="pub-item with-icon">
            <div class="content-wrapper">
                <h3 class="title">
                    <a href="/yayin/11111111-1111-4111-8111-111111111111/article">
                        <strong>Örnek Makale</strong>
                    </a>
                </h3>

                <div class="description">
                    <div class="citation">Yazar A., Yazar B.</div>
                    <div class="citation">
                        Örnek Dergi, cilt.5, ss.10-20, 2026
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    items = parse_publication_list(html)

    assert len(items) == 1
    assert items[0].citation_text == (
        "Örnek Dergi, cilt.5, ss.10-20, 2026"
    )
    assert items[0].year == 2026