import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_DIR / "data" / "faculty_catalog.csv"

REQUIRED_COLUMNS = {
    "id",
    "full_name",
    "unit",
    "profile_url",
    "is_active",
}


@dataclass(frozen=True)
class Faculty:
    id: str
    full_name: str
    unit: str
    profile_url: str


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
                f"Akademisyen katalog dosyasında eksik kolonlar var: {missing}"
            )

        faculties: list[Faculty] = []

        for row in reader:
            if not _is_active(row["is_active"]):
                continue

            faculty = Faculty(
                id=row["id"].strip(),
                full_name=row["full_name"].strip(),
                unit=row["unit"].strip(),
                profile_url=row["profile_url"].strip(),
            )

            _validate_faculty(faculty)
            faculties.append(faculty)

    return sorted(faculties, key=lambda faculty: faculty.full_name.casefold())


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

    if not faculty.full_name:
        raise ValueError(
            f"'{faculty.id}' kaydında akademisyenin adı boş."
        )

    if not faculty.unit:
        raise ValueError(
            f"'{faculty.id}' kaydında birim bilgisi boş."
        )

    if not faculty.profile_url.startswith("https://avesis.deu.edu.tr/"):
        raise ValueError(
            f"'{faculty.id}' kaydında geçersiz AVESİS profil URL'si var."
        )