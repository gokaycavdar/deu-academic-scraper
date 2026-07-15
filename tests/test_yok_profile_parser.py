import pytest

from app.services.yok.profile_parser import parse_profile_sections


def test_parses_profile_section_links() -> None:
    html = """
    <html>
      <body>
        <a href="/AkademikArama/AkademisyenArama?islem=test">
          Kitaplar
        </a>

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
      </body>
    </html>
    """

    sections = parse_profile_sections(html)

    assert sections == {
        "book": (
            "https://akademik.yok.gov.tr/AkademikArama/"
            "AkademisyenYayinBilgileri?pubType=book"
        ),
        "article": (
            "https://akademik.yok.gov.tr/AkademikArama/"
            "AkademisyenYayinBilgileri?pubType=article"
        ),
        "conference_paper": (
            "https://akademik.yok.gov.tr/AkademikArama/"
            "AkademisyenYayinBilgileri?pubType=proceeding"
        ),
        "project": (
            "https://akademik.yok.gov.tr/AkademikArama/"
            "AkademisyenProjeBilgileri?authorId=test"
        ),
        "patent": (
            "https://akademik.yok.gov.tr/AkademikArama/"
            "AkademisyenPatentBilgileri?authorId=test"
        ),
    }


def test_rejects_profile_with_missing_section() -> None:
    html = """
    <a href="/AkademikArama/AkademisyenYayinBilgileri?pubType=book">
      Kitaplar
    </a>
    """

    with pytest.raises(ValueError, match="eksik kayıt türü menüleri"):
        parse_profile_sections(html)