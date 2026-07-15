from openpyxl import load_workbook

from app.services.avesis.normalizer import NormalizedRecord
from app.services.excel_exporter import ExcelExporter
from app.services.faculty_catalog import Faculty
from app.services.record_filter import YearScope


def test_exports_summary_and_selected_record_sheets(
    tmp_path,
) -> None:
    academician = Faculty(
        id="gokhan-dalkilic",
        full_name="Gökhan Dalkılıç",
        unit="Mühendislik Fakültesi / Bilgisayar Mühendisliği",
        profile_url="https://avesis.deu.edu.tr/gokhan.dalkilic",
        sort_order=10,
    )

    article = NormalizedRecord(
        academician_id=academician.id,
        academician_name=academician.full_name,
        record_id="article-test",
        record_type="article",
        title="Test Makalesi",
        contributor_names="Yazar A., Yazar B.",
        contributor_text="Yazar A., Yazar B.",
        source_url="https://avesis.deu.edu.tr/yayin/article-test",
        citation_text="Test Dergisi, 2026",
        year=2026,
        data={
            "journal_name": "Test Dergisi",
            "volume": "15",
            "issue": "2",
            "pages": "ss.10-20",
            "doi": "10.1000/test",
            "journal_indexes": "Scopus",
        },
    )

    patent = NormalizedRecord(
        academician_id=academician.id,
        academician_name=academician.full_name,
        record_id="patent-test",
        record_type="patent",
        title="Test Patenti",
        contributor_names="Mucit A.",
        contributor_text="Mucit A.",
        source_url=(
            "https://avesis.deu.edu.tr/"
            "fikrimulkiyet/patent-test"
        ),
        citation_text="Patent, BÖLÜM G Fizik",
        year=2024,
        data={
            "intellectual_property": "Patent",
            "patent_class": "BÖLÜM G Fizik",
            "registration_number": "2024 00001",
            "registration_type": "Standart Tescil",
            "application_country": "Türkiye",
            "application_date": "01.01.2023",
            "registration_date": "01.01.2024",
            "status": "Tescil Edildi",
        },
    )

    output_path = tmp_path / "akademik_rapor.xlsx"

    ExcelExporter().export(
        records=[article, patent],
        academicians=[academician],
        selected_record_types={"article", "patent"},
        year_scope=YearScope.all_years(),
        output_path=output_path,
    )

    workbook = load_workbook(output_path)

    try:
        assert workbook.sheetnames == [
            "00_Ozet",
            "01_Makaleler",
            "05_Patentler",
        ]

        summary_sheet = workbook["00_Ozet"]

        assert summary_sheet["A1"].value == (
            "DEÜ AVESİS Akademik Rapor"
        )
        assert summary_sheet["C8"].value == 1
        assert summary_sheet["D8"].value == 1
        assert summary_sheet["E8"].value == 2
        assert summary_sheet["F8"].value == 0

        article_sheet = workbook["01_Makaleler"]

        assert article_sheet["C2"].value == "Test Makalesi"
        assert article_sheet["E2"].value == "Test Dergisi"
        assert article_sheet["I2"].value == "10.1000/test"
        assert article_sheet["K2"].value == "Aç"
        assert article_sheet["K2"].hyperlink.target == (
            "https://avesis.deu.edu.tr/yayin/article-test"
        )

        patent_sheet = workbook["05_Patentler"]

        assert patent_sheet["B2"].value == "Test Patenti"
        assert patent_sheet["F2"].value == "2024 00001"
        assert patent_sheet["K2"].value == "Tescil Edildi"
        assert patent_sheet["L2"].value == "Aç"
    finally:
        workbook.close()