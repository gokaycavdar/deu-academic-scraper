from app.services.yok.activity_list_parser import (
    parse_activity_list,
)


def test_parses_project_list_item() -> None:
    html = """
    <div class="projectmain">
      <span class="baslika">
        <strong>Test Projesi</strong>
      </span>

      <a class="popoverData">YAZAR BİR</a>,
      <a class="popoverData">YAZAR İKİ</a>

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
        , 01.03.2020 - 31.07.2021, 498000 TÜRK LİRASI
      </div>
    </div>
    """

    items = parse_activity_list(
        html,
        record_type="project",
    )

    assert len(items) == 1

    item = items[0]

    assert item.record_type == "project"
    assert item.title == "Test Projesi"
    assert item.contributor_names == "YAZAR BİR, YAZAR İKİ"
    assert item.year == 2020
    assert item.data == {
        "supporting_organization": (
            "DOKUZ EYLÜL ÜNİVERSİTESİ"
        ),
        "project_type": "TÜBİTAK PROJESİ",
        "status": "Tamamlandı",
        "start_date": "01.03.2020",
        "end_date": "31.07.2021",
        "start_year": "2020",
        "end_year": "2021",
        "budget_amount": "498000",
        "budget_currency": "TÜRK LİRASI",
    }


def test_parses_patent_list_item() -> None:
    html = """
    <div class="projectmain">
      <h5 class="projectTitle">
        <strong>
          TEST PATENTİ 2018/05933
        </strong>
      </h5>

      <div class="projectAuthor">
        Patent Başvuru Sahipleri :Dokuz Eylül Üniversitesi
        Patent Buluş Sahipleri:Ömer Aydın,Umut Can Çabuk,
        Gökhan Dalkılıç
      </div>

      <div class="projectType">
        <span class="label label-info">Patent</span>
        <span class="label label-success">
          SECTION G - PHYSICS
        </span>
      </div>
    </div>
    """

    items = parse_activity_list(
        html,
        record_type="patent",
    )

    assert len(items) == 1

    item = items[0]

    assert item.record_type == "patent"
    assert item.title == "TEST PATENTİ"
    assert item.contributor_names == (
        "Ömer Aydın, Umut Can Çabuk, Gökhan Dalkılıç"
    )
    assert item.year == 2018
    assert item.data == {
        "intellectual_property": "Patent",
        "patent_class": "SECTION G - PHYSICS",
        "registration_number": "2018/05933",
        "applicants": "Dokuz Eylül Üniversitesi",
        "inventors": (
            "Ömer Aydın, Umut Can Çabuk, Gökhan Dalkılıç"
        ),
    }