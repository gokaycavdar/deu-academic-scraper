import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_DIR / "data" / "faculty_catalog.csv"

REQUIRED_COLUMNS = {
    "id",
    "sort_order",
    "academic_title",
    "full_name",
    "unit",
    "profile_url",
    "yok_author_id",
    "yok_profile_sira",
    "is_active",
}


@dataclass(frozen=True)
class Faculty:
    id: str
    sort_order: int
    full_name: str
    unit: str
    profile_url: str
    academic_title: str = ""
    yok_author_id: str = ""
    yok_profile_sira: str = ""


def load_active_faculties(
    catalog_path: Path = CATALOG_PATH,
) -> list[Faculty]:
    with catalog_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        available_columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - available_columns

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(
                "Akademisyen katalog dosyasında eksik kolonlar var: "
                f"{missing}"
            )

        faculties: list[Faculty] = []
        seen_ids: set[str] = set()

        for row in reader:
            if not _is_active(row["is_active"]):
                continue

            faculty = Faculty(
                id=row["id"].strip(),
                sort_order=_parse_sort_order(
                    row["sort_order"],
                    row["id"],
                ),
                academic_title=row["academic_title"].strip(),
                full_name=row["full_name"].strip(),
                unit=row["unit"].strip(),
                profile_url=row["profile_url"].strip(),
                yok_author_id=row["yok_author_id"].strip(),
                yok_profile_sira=row["yok_profile_sira"].strip(),
            )

            _validate_faculty(faculty)

            if faculty.id in seen_ids:
                raise ValueError(
                    "Akademisyen kataloğunda yinelenen id var: "
                    f"{faculty.id}"
                )

            seen_ids.add(faculty.id)
            faculties.append(faculty)

    return sorted(
        faculties,
        key=lambda faculty: (
            faculty.sort_order,
            faculty.full_name.casefold(),
        ),
    )


def _parse_sort_order(
    value: str | None,
    faculty_id: str,
) -> int:
    try:
        sort_order = int((value or "").strip())
    except ValueError as error:
        raise ValueError(
            f"'{faculty_id}' kaydında geçersiz sort_order değeri var."
        ) from error

    if sort_order < 1:
        raise ValueError(
            f"'{faculty_id}' kaydında sort_order pozitif olmalıdır."
        )

    return sort_order


def _is_active(value: str | None) -> bool:
    return (value or "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "evet",
    }


def _validate_faculty(faculty: Faculty) -> None:
    if not faculty.id:
        raise ValueError("Akademisyen kataloğunda boş 'id' değeri var.")

    if not faculty.academic_title:
        raise ValueError(
            f"'{faculty.id}' kaydında akademik unvan boş."
        )

    if not faculty.full_name:
        raise ValueError(
            f"'{faculty.id}' kaydında akademisyenin adı boş."
        )

    if not faculty.unit:
        raise ValueError(
            f"'{faculty.id}' kaydında birim bilgisi boş."
        )

    if not faculty.profile_url.startswith(
        "https://avesis.deu.edu.tr/"
    ):
        raise ValueError(
            f"'{faculty.id}' kaydında geçersiz AVESİS profil URL'si var."
        )

    if not faculty.yok_author_id:
        raise ValueError(
            f"'{faculty.id}' kaydında YÖK authorId boş."
        )

    if not faculty.yok_profile_sira:
        raise ValueError(
            f"'{faculty.id}' kaydında YÖK profil sira değeri boş."
        )