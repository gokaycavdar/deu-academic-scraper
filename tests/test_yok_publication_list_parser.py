from app.services.yok.publication_list_parser import (
    parse_publication_list,
)


def test_parses_article_list_item() -> None:
    html = """
    <table>
      <tr>
        <td><span class="badge">1</span></td>
        <td>
          <span class="baslika">
            <strong>
              <a
                data-target="#remoteModal"
                href="yayinDetay.jsp?id=article-id&no=article-no"
              >
                Test Makalesi
              </a>
            </strong>
          </span>

          <a class="popoverData">YAZAR BİR</a>,
          <a class="popoverData">YAZAR İKİ</a>,

          Yayın Yeri:Test Journal, 2024

          <p>
            <span class="label label-info">Uluslararası</span>
            <span class="label label-primary">Hakemli</span>
            <span class="label label-success">SCI-Expanded</span>
            <span class="label label-default">Özgün Makale</span>
            <a href="https://dx.doi.org/10.1000/test">
              https://dx.doi.org/10.1000/test
            </a>
          </p>
        </td>
      </tr>
    </table>
    """

    items = parse_publication_list(
        html,
        record_type="article",
        page_url=(
            "https://akademik.yok.gov.tr/AkademikArama/"
            "view/viewAuthorArticle.jsp"
        ),
    )

    assert len(items) == 1

    item = items[0]

    assert item.record_type == "article"
    assert item.title == "Test Makalesi"
    assert item.contributor_names == "YAZAR BİR, YAZAR İKİ"
    assert item.year == 2024
    assert item.detail_url == (
        "https://akademik.yok.gov.tr/AkademikArama/"
        "view/yayinDetay.jsp?id=article-id&no=article-no"
    )
    assert item.data == {
        "venue": "Test Journal",
        "scope": "Uluslararası",
        "doi": "https://dx.doi.org/10.1000/test",
        "peer_review": "Hakemli",
        "index_type": "SCI-Expanded",
        "publication_type": "Özgün Makale",
    }


def test_parses_conference_list_item() -> None:
    html = """
    <table>
      <tr>
        <td><span class="badge">1</span></td>
        <td>
          <strong>
            <a
              data-target="#remoteModal"
              href="yayinDetay.jsp?id=conference-id&no=conference-no"
            >
              Test Bildirisi
            </a>
          </strong>

          <a class="popoverData">YAZAR BİR</a>,
          <a class="popoverData">YAZAR İKİ</a>

          (27.06.2025 - 28.06.2025),
          Yayın Yeri:Test Konferansı, 2025

          <p>
            <span class="label label-info">Uluslararası</span>
            <span class="label label-success">
              Tam metin bildiri
            </span>
          </p>
        </td>
      </tr>
    </table>
    """

    items = parse_publication_list(
        html,
        record_type="conference_paper",
        page_url=(
            "https://akademik.yok.gov.tr/AkademikArama/"
            "view/viewAuthorProceeding.jsp"
        ),
    )

    assert len(items) == 1

    item = items[0]

    assert item.title == "Test Bildirisi"
    assert item.year == 2025
    assert item.data["venue"] == "Test Konferansı"
    assert item.data["scope"] == "Uluslararası"
    assert item.data["index_type"] == "Tam metin bildiri"
    assert item.data["start_date"] == "27.06.2025"
    assert item.data["end_date"] == "28.06.2025"


def test_parses_book_chapter_list_item() -> None:
    html = """
    <div class="projects">
      <div class="row">
        <div class="col-lg-11 col-md-10">
          <strong>1. Akıllı Teknoloji ve Akıllı Yönetim</strong>

          <p>
            Bölüm Adı:Nesnelerin İnterneti için Sayı Üreteci,
            AYDIN ÖMER,DALKILIÇ GÖKHAN,
            Yayın Yeri:Gülermat Matbaacılık,
            Editör:TECİM Vahap, TARHAN Çiğdem,
            Basım sayısı:1,
            ISBN:9786056004759,
            Bölüm Sayfaları:121 -129
          </p>

          <p>
            <span class="label label-info">2016</span>
            <span class="label label-primary">Bilimsel Kitap</span>
            <span class="label label-success">Kitap Bölümü</span>
          </p>
        </div>
      </div>
    </div>
    """

    items = parse_publication_list(
        html,
        record_type="book",
        page_url=(
            "https://akademik.yok.gov.tr/AkademikArama/"
            "view/viewAuthorBook.jsp"
        ),
    )

    assert len(items) == 1

    item = items[0]

    assert item.record_type == "book"
    assert item.title == "Nesnelerin İnterneti için Sayı Üreteci"
    assert item.contributor_names == (
        "AYDIN ÖMER, DALKILIÇ GÖKHAN"
    )
    assert item.year == 2016
    assert item.detail_url is None
    assert item.data == {
        "book_title": "Akıllı Teknoloji ve Akıllı Yönetim",
        "publisher": "Gülermat Matbaacılık",
        "editors": "TECİM Vahap, TARHAN Çiğdem",
        "edition": "1",
        "page_count": None,
        "isbn": "9786056004759",
        "chapter_pages": "121 -129",
        "publication_type": "Bilimsel Kitap",
        "book_kind": "Kitap Bölümü",
    }


def test_parses_full_book_list_item() -> None:
    html = """
    <div class="projects">
      <div class="row">
        <div class="col-lg-11 col-md-10">
          <strong>5. Test Kitabı</strong>

          <p>
            YAZAR BİR,YAZAR İKİ,
            Yayın Yeri:Test Yayınevi, İzmir,
            Basım sayısı:2,
            Sayfa sayısı:351,
            ISBN:123-456
          </p>

          <p>
            <span class="label label-info">2020</span>
            <span class="label label-primary">Ders Kitabı</span>
          </p>
        </div>
      </div>
    </div>
    """

    items = parse_publication_list(
        html,
        record_type="book",
        page_url=(
            "https://akademik.yok.gov.tr/AkademikArama/"
            "view/viewAuthorBook.jsp"
        ),
    )

    assert len(items) == 1

    item = items[0]

    assert item.record_type == "book"
    assert item.title == "Test Kitabı"
    assert item.contributor_names == "YAZAR BİR, YAZAR İKİ"
    assert item.year == 2020
    assert item.detail_url is None
    assert item.data == {
        "book_title": None,
        "publisher": "Test Yayınevi, İzmir",
        "editors": None,
        "edition": "2",
        "page_count": "351",
        "isbn": "123-456",
        "chapter_pages": None,
        "publication_type": "Ders Kitabı",
        "book_kind": None,
    }


def test_deduplicates_repeated_detail_url() -> None:
    html = """
    <table>
      <tr>
        <td>
          <a data-target="#remoteModal"
             href="yayinDetay.jsp?id=same-record">
            First rendering
          </a>
          <a class="popoverData">GÖKHAN DALKILIÇ</a>
          Yayın Yeri: Test Journal, 2026
          <span class="label label-info">Uluslararası</span>
          <span class="label label-primary">Hakemli</span>
          <span class="label label-success">SCI-Expanded</span>
          <span class="label label-default">Özgün Makale</span>
        </td>
      </tr>
      <tr>
        <td>
          <a data-target="#remoteModal"
             href="yayinDetay.jsp?id=same-record">
            Second rendering
          </a>
          <a class="popoverData">GÖKHAN DALKILIÇ</a>
          Yayın Yeri: Test Journal, 2026
          <span class="label label-info">Uluslararası</span>
          <span class="label label-primary">Hakemli</span>
          <span class="label label-success">SCI-Expanded</span>
          <span class="label label-default">Özgün Makale</span>
        </td>
      </tr>
    </table>
    """

    items = parse_publication_list(
        html,
        record_type="article",
        page_url=(
            "https://akademik.yok.gov.tr/AkademikArama/"
            "view/viewAuthorArticle.jsp"
        ),
    )

    assert len(items) == 1
    assert items[0].detail_url == (
        "https://akademik.yok.gov.tr/AkademikArama/"
        "view/yayinDetay.jsp?id=same-record"
    )