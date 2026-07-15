from app.services.faculty_catalog import Faculty
from app.services.record_filter import YearScope
from app.services.yok.client import YokPage
from app.services.yok.report_collector import (
    YokReportCollector,
)


PROFILE_URL = (
    "https://akademik.yok.gov.tr/"
    "AkademikArama/view/viewAuthor.jsp"
)

ARTICLE_SECTION_URL = (
    "https://akademik.yok.gov.tr/"
    "AkademikArama/AkademisyenYayinBilgileri?pubType=article"
)

ARTICLE_DETAIL_URL = (
    "https://akademik.yok.gov.tr/"
    "AkademikArama/view/yayinDetay.jsp?id=1"
)

PROJECT_SECTION_URL = (
    "https://akademik.yok.gov.tr/"
    "AkademikArama/AkademisyenProjeBilgileri?authorId=test"
)

PROFILE_HTML = """
<a href="/AkademikArama/AkademisyenYayinBilgileri?pubType=book">
  Kitaplar
</a>
<a href="/AkademikArama/AkademisyenYayinBilgileri?pubType=article">
  Makaleler
</a>
<a href="/AkademikArama/AkademisyenYayinBilgileri?pubType=proceeding">
  Bildiriler
</a>
<a href="/AkademikArama/AkademisyenProjeBilgileri?authorId=test">
  Projeler
</a>
<a href="/AkademikArama/AkademisyenPatentBilgileri?authorId=test">
  Patentler
</a>
"""


class FakeYokClient:
    def __init__(self, pages: dict[str, YokPage]) -> None:
        self.pages = pages
        self.opened_author_id: str | None = None
        self.opened_profile_sira: str | None = None

    def open_academician_profile(
        self,
        *,
        author_id: str,
        profile_sira: str,
    ) -> YokPage:
        self.opened_author_id = author_id
        self.opened_profile_sira = profile_sira

        return self.pages[PROFILE_URL]

    def get_html(
        self,
        url: str,
        *,
        referer_url: str | None = None,
    ) -> YokPage:
        return self.pages[url]


def make_page(url: str, html: str) -> YokPage:
    return YokPage(
        url=url,
        status_code=200,
        html=html,
    )


def make_academician() -> Faculty:
    return Faculty(
        id="gokhan-dalkilic",
        sort_order=1,
        full_name="Gökhan Dalkılıç",
        unit="Mühendislik Fakültesi / Bilgisayar Mühendisliği",
        profile_url="https://avesis.deu.edu.tr/gokhan.dalkilic",
        yok_author_id="TEST_AUTHOR_ID",
        yok_profile_sira="TEST_SIRA",
    )


def test_collects_filtered_article_and_detail_fields() -> None:
    article_html = """
    <table>
      <tr>
        <td>
          <a data-target="#remoteModal"
             href="/AkademikArama/view/yayinDetay.jsp?id=1">
            Test Article
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

    detail_html = """
    <div class="modal-body">
      <div class="te">
        <strong>Yayın Yeri:</strong>
        Test Journal
      </div>
      <div class="te">
        <strong>DOI:</strong>
        https://dx.doi.org/10.1000/test
      </div>
      <div class="te">
        <strong>ISSN:</strong>
        1234-5678
      </div>
    </div>
    """

    client = FakeYokClient(
        {
            PROFILE_URL: make_page(
                PROFILE_URL,
                PROFILE_HTML,
            ),
            ARTICLE_SECTION_URL: make_page(
                ARTICLE_SECTION_URL,
                article_html,
            ),
            ARTICLE_DETAIL_URL: make_page(
                ARTICLE_DETAIL_URL,
                detail_html,
            ),
        }
    )

    result = YokReportCollector(client).collect_records(
        academicians=[make_academician()],
        selected_record_types={"article"},
        year_scope=YearScope.single_year(2026),
    )

    assert result.issues == []
    assert client.opened_author_id == "TEST_AUTHOR_ID"
    assert client.opened_profile_sira == "TEST_SIRA"
    assert len(result.records) == 1

    record = result.records[0]

    assert record.title == "Test Article"
    assert record.year == 2026
    assert record.source_names == ("YÖK Akademik",)
    assert record.data["doi"] == "10.1000/test"
    assert record.data["journal_indexes"] == "SCI-Expanded"
    assert record.data["issn"] == "1234-5678"


def test_filters_project_by_date_range() -> None:
    project_html = """
    <div class="projectmain">
      <div class="baslika">
        <strong>Test Projesi</strong>
      </div>

      <a class="popoverData">GÖKHAN DALKILIÇ</a>

      <div class="projectType">
        <span class="label label-default">
          DOKUZ EYLÜL ÜNİVERSİTESİ
        </span>
        <span class="label label-primary">
          TÜBİTAK PROJESİ
        </span>
        <span class="label label-success">
          Tamamlandı
        </span>
        01.03.2013 - 31.07.2014, 498000 TÜRK LİRASI
      </div>
    </div>
    """

    client = FakeYokClient(
        {
            PROFILE_URL: make_page(
                PROFILE_URL,
                PROFILE_HTML,
            ),
            PROJECT_SECTION_URL: make_page(
                PROJECT_SECTION_URL,
                project_html,
            ),
        }
    )

    result = YokReportCollector(client).collect_records(
        academicians=[make_academician()],
        selected_record_types={"project"},
        year_scope=YearScope.single_year(2014),
    )

    assert result.issues == []
    assert len(result.records) == 1

    record = result.records[0]

    assert record.title == "Test Projesi"
    assert record.data["start_year"] == 2013
    assert record.data["end_year"] == 2014
    assert record.data["budget_amount"] == "498000"