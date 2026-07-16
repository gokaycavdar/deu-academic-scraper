from app.services.avesis.normalizer import NormalizedRecord
from app.services.record_merger import merge_source_records


def make_record(
    *,
    source_name: str,
    record_id: str,
    record_type: str = "article",
    title: str = "Secure IoT Communication",
    year: int | None = 2025,
    contributors: str = "DALKILIÇ G.",
    data: dict[str, str | int | None] | None = None,
) -> NormalizedRecord:
    return NormalizedRecord(
        academician_id="gokhan-dalkilic",
        academician_name="Gökhan Dalkılıç",
        record_id=record_id,
        record_type=record_type,
        title=title,
        contributor_names=contributors,
        contributor_text=contributors,
        source_url=(
            "https://avesis.deu.edu.tr/yayin/test"
            if source_name == "AVESİS"
            else ""
        ),
        citation_text="",
        year=year,
        data=data or {},
        source_names=(source_name,),
    )


def test_merges_single_exact_title_match() -> None:
    avesis_record = make_record(
        source_name="AVESİS",
        record_id="avesis-1",
        title="CoMAD: Context-Aware Mutual Authentication",
        data={
            "journal_name": "IEEE Access",
            "doi": "10.1109/ACCESS.2021.3083549",
            "scope": None,
            "peer_review": None,
            "issn": None,
        },
    )
    yok_record = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        title="COMAD Context Aware Mutual Authentication",
        contributors=(
            "UMUT CAN ÇABUK, GÖKHAN DALKILIÇ"
        ),
        data={
            "journal_name": "IEEE ACCESS",
            "doi": (
                "https://dx.doi.org/"
                "10.1109/ACCESS.2021.3083549"
            ),
            "scope": "Uluslararası",
            "peer_review": "Hakemli",
            "issn": "2169-3536",
        },
    )

    records = merge_source_records(
        [avesis_record],
        [yok_record],
    )

    assert len(records) == 1

    record = records[0]
    assert record.record_id == "avesis-1"
    assert record.source_names == (
        "AVESİS",
        "YÖK Akademik",
    )
    assert record.data["journal_name"] == "IEEE Access"
    assert record.data["scope"] == "Uluslararası"
    assert record.data["peer_review"] == "Hakemli"
    assert record.data["issn"] == "2169-3536"


def test_keeps_yok_only_record() -> None:
    yok_record = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        title="Only in YÖK",
        data={"scope": "Uluslararası"},
    )

    records = merge_source_records([], [yok_record])

    assert records == [yok_record]


def test_uses_doi_for_repeated_title() -> None:
    avesis_first = make_record(
        source_name="AVESİS",
        record_id="avesis-1",
        title="Repeated Title",
        year=2023,
        data={"doi": "10.1000/first", "scope": None},
    )
    avesis_second = make_record(
        source_name="AVESİS",
        record_id="avesis-2",
        title="Repeated Title",
        year=2024,
        data={"doi": "10.1000/second", "scope": None},
    )
    yok_first = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        title="Repeated Title",
        year=2024,
        data={
            "doi": "https://doi.org/10.1000/second",
            "scope": "Uluslararası",
        },
    )
    yok_second = make_record(
        source_name="YÖK Akademik",
        record_id="yok-2",
        title="Repeated Title",
        year=2023,
        data={
            "doi": "https://doi.org/10.1000/first",
            "scope": "Ulusal",
        },
    )

    records = merge_source_records(
        [avesis_first, avesis_second],
        [yok_first, yok_second],
    )

    assert len(records) == 2

    records_by_id = {
        record.record_id: record
        for record in records
    }

    assert records_by_id["avesis-1"].data["scope"] == "Ulusal"
    assert records_by_id["avesis-2"].data["scope"] == "Uluslararası"


def test_leaves_ambiguous_repeated_titles_separate() -> None:
    avesis_first = make_record(
        source_name="AVESİS",
        record_id="avesis-1",
        title="Repeated Title",
        year=2024,
        contributors="DALKILIÇ G.",
    )
    avesis_second = make_record(
        source_name="AVESİS",
        record_id="avesis-2",
        title="Repeated Title",
        year=2024,
        contributors="DALKILIÇ G.",
    )
    yok_record = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        title="Repeated Title",
        year=2024,
        contributors="GÖKHAN DALKILIÇ",
    )

    records = merge_source_records(
        [avesis_first, avesis_second],
        [yok_record],
    )

    assert len(records) == 3
    assert all(
        record.source_names != (
            "AVESİS",
            "YÖK Akademik",
        )
        for record in records
    )

def test_merges_same_article_doi_with_different_titles() -> None:
    avesis_record = make_record(
        source_name="AVESİS",
        record_id="avesis-1",
        record_type="article",
        title="Secure Communication for Drone Networks",
        data={
            "doi": "10.1000/shared-doi",
            "scope": None,
        },
    )
    yok_record = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        record_type="article",
        title="İnsansız Hava Araçları İçin Güvenli Haberleşme",
        data={
            "doi": "https://dx.doi.org/10.1000/SHARED-DOI",
            "scope": "Uluslararası",
        },
    )

    records = merge_source_records(
        [avesis_record],
        [yok_record],
    )

    assert len(records) == 1

    record = records[0]

    assert record.title == "Secure Communication for Drone Networks"
    assert record.source_names == (
        "AVESİS",
        "YÖK Akademik",
    )
    assert record.data["scope"] == "Uluslararası"


def test_keeps_same_conference_title_separate_when_dois_differ() -> None:
    avesis_record = make_record(
        source_name="AVESİS",
        record_id="avesis-1",
        record_type="conference_paper",
        title="Same Conference Paper",
        data={"doi": "10.1000/first-doi"},
    )
    yok_record = make_record(
        source_name="YÖK Akademik",
        record_id="yok-1",
        record_type="conference_paper",
        title="Same Conference Paper",
        data={"doi": "10.1000/second-doi"},
    )

    records = merge_source_records(
        [avesis_record],
        [yok_record],
    )

    assert len(records) == 2
    assert records[0].source_names == ("AVESİS",)
    assert records[1].source_names == ("YÖK Akademik",) 