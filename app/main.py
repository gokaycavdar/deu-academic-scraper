from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from app.services.avesis.client import AvesisClient
from app.services.excel_exporter import (
    ExcelExporter,
    RECORD_TYPE_LABELS,
    RECORD_TYPE_ORDER,
)
from app.services.faculty_catalog import Faculty, load_active_faculties
from app.services.record_filter import YearScope
from app.services.report_service import ReportService, SUPPORTED_RECORD_TYPES


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
GENERATED_REPORTS_DIR = PROJECT_DIR / "data" / "generated" / "web"

CURRENT_YEAR = datetime.now().year
YEAR_OPTIONS = tuple(
    str(year)
    for year in range(CURRENT_YEAR, 1899, -1)
)

RECORD_TYPE_OPTIONS = tuple(
    (record_type, RECORD_TYPE_LABELS[record_type])
    for record_type in RECORD_TYPE_ORDER
)

app = FastAPI(
    title="DEÜ AVESİS Akademik Rapor",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=APP_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/", response_class=HTMLResponse, tags=["Sistem"])
def home(request: Request):
    return _render_home(request)


@app.post("/reports/export", name="export_report")
def export_report(
    request: Request,
    academician_ids: list[str] = Form(default=[]),
    record_types: list[str] = Form(default=[]),
    period_mode: str = Form(default="single"),
    single_year: str | None = Form(default=None),
    start_year: str | None = Form(default=None),
    end_year: str | None = Form(default=None),
):
    selected_academician_ids = set(academician_ids)
    selected_record_types = set(record_types)

    try:
        academicians = load_active_faculties()
        selected_academicians = _select_academicians(
            academicians,
            selected_academician_ids,
        )
        selected_record_types = _validate_record_types(
            selected_record_types,
        )
        year_scope = _build_year_scope(
            period_mode=period_mode,
            single_year=single_year,
            start_year=start_year,
            end_year=end_year,
        )
    except ValueError as error:
        return _render_home(
            request,
            status_code=422,
            error_message=str(error),
            selected_academician_ids=selected_academician_ids,
            selected_record_types=selected_record_types,
            period_mode=period_mode,
            single_year=single_year,
            start_year=start_year,
            end_year=end_year,
        )

    client = AvesisClient()

    try:
        result = ReportService(client).collect_records(
            academicians=selected_academicians,
            selected_record_types=selected_record_types,
            year_scope=year_scope,
        )
    finally:
        client.close()

    if result.issues:
        return _render_home(
            request,
            status_code=502,
            error_message=(
                "AVESİS'ten bazı kayıtlar okunamadı. "
                "Rapor eksik olmaması için oluşturulmadı; "
                "lütfen yeniden deneyin."
            ),
            selected_academician_ids=selected_academician_ids,
            selected_record_types=selected_record_types,
            period_mode=period_mode,
            single_year=single_year,
            start_year=start_year,
            end_year=end_year,
        )

    if not result.records:
        return _render_home(
            request,
            status_code=422,
            error_message="Seçiminizle eşleşen kayıt bulunamadı.",
            selected_academician_ids=selected_academician_ids,
            selected_record_types=selected_record_types,
            period_mode=period_mode,
            single_year=single_year,
            start_year=start_year,
            end_year=end_year,
        )

    report_path = _create_report_path()

    ExcelExporter().export(
        records=result.records,
        academicians=selected_academicians,
        selected_record_types=selected_record_types,
        year_scope=year_scope,
        output_path=report_path,
    )

    download_name = (
        "deu_avesis_akademik_rapor_"
        f"{datetime.now():%Y-%m-%d_%H-%M}.xlsx"
    )

    return FileResponse(
        path=report_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        filename=download_name,
        background=BackgroundTask(
            _delete_generated_report,
            report_path,
        ),
    )


@app.get("/health", tags=["Sistem"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _render_home(
    request: Request,
    *,
    status_code: int = 200,
    error_message: str | None = None,
    selected_academician_ids: set[str] | None = None,
    selected_record_types: set[str] | None = None,
    period_mode: str = "single",
    single_year: str | None = None,
    start_year: str | None = None,
    end_year: str | None = None,
):
    if selected_academician_ids is None:
        selected_academician_ids = set()

    if selected_record_types is None:
        selected_record_types = set(RECORD_TYPE_ORDER)

    return templates.TemplateResponse(
        request=request,
        name="reports/index.html",
        status_code=status_code,
        context={
            "page_title": "Akademik Rapor Oluştur",
            "academicians": load_active_faculties(),
            "record_type_options": RECORD_TYPE_OPTIONS,
            "year_options": YEAR_OPTIONS,
            "error_message": error_message,
            "selected_academician_ids": selected_academician_ids,
            "selected_record_types": selected_record_types,
            "period_mode": period_mode,
            "single_year": single_year or str(CURRENT_YEAR),
            "start_year": start_year or str(CURRENT_YEAR),
            "end_year": end_year or str(CURRENT_YEAR),
        },
    )


def _select_academicians(
    academicians: list[Faculty],
    selected_academician_ids: set[str],
) -> list[Faculty]:
    if not selected_academician_ids:
        raise ValueError("En az bir akademisyen seçmelisiniz.")

    available_ids = {
        academician.id
        for academician in academicians
    }

    unknown_ids = selected_academician_ids - available_ids

    if unknown_ids:
        raise ValueError("Geçersiz akademisyen seçimi yapıldı.")

    return [
        academician
        for academician in academicians
        if academician.id in selected_academician_ids
    ]


def _validate_record_types(
    selected_record_types: set[str],
) -> set[str]:
    if not selected_record_types:
        raise ValueError("En az bir kayıt türü seçmelisiniz.")

    unsupported_types = (
        selected_record_types - SUPPORTED_RECORD_TYPES
    )

    if unsupported_types:
        raise ValueError("Geçersiz kayıt türü seçimi yapıldı.")

    return selected_record_types


def _build_year_scope(
    *,
    period_mode: str,
    single_year: str | None,
    start_year: str | None,
    end_year: str | None,
) -> YearScope:
    if period_mode == "all":
        return YearScope.all_years()

    if period_mode == "single":
        return YearScope.single_year(
            _parse_year(single_year, "Yıl"),
        )

    if period_mode == "range":
        return YearScope(
            start_year=_parse_year(
                start_year,
                "Başlangıç yılı",
            ),
            end_year=_parse_year(
                end_year,
                "Bitiş yılı",
            ),
        )

    raise ValueError("Geçersiz zaman kapsamı seçimi yapıldı.")


def _parse_year(value: str | None, label: str) -> int:
    try:
        year = int(value or "")
    except ValueError as error:
        raise ValueError(f"{label} seçmelisiniz.") from error

    if year < 1900 or year > CURRENT_YEAR:
        raise ValueError(f"{label} geçerli bir yıl olmalıdır.")

    return year


def _create_report_path() -> Path:
    GENERATED_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid4().hex[:8]

    return (
        GENERATED_REPORTS_DIR
        / f"akademik_rapor_{timestamp}_{unique_suffix}.xlsx"
    )


def _delete_generated_report(report_path: Path) -> None:
    report_path.unlink(missing_ok=True)