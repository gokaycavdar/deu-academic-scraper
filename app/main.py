from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import (
    BackgroundTasks,
    FastAPI,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.avesis.client import AvesisClient
from app.services.excel_exporter import (
    ExcelExporter,
    RECORD_TYPE_LABELS,
    RECORD_TYPE_ORDER,
)
from app.services.faculty_catalog import Faculty, load_active_faculties
from app.services.record_filter import YearScope
from app.services.report_job_store import ReportJobStore
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

report_jobs = ReportJobStore()

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
    return templates.TemplateResponse(
        request=request,
        name="reports/index.html",
        context={
            "page_title": "Akademik Rapor Oluştur",
            "academicians": load_active_faculties(),
            "record_type_options": RECORD_TYPE_OPTIONS,
            "year_options": YEAR_OPTIONS,
            "current_year": str(CURRENT_YEAR),
        },
    )


@app.post("/reports", name="start_report")
def start_report(
    request: Request,
    background_tasks: BackgroundTasks,
    academician_ids: list[str] = Form(default=[]),
    record_types: list[str] = Form(default=[]),
    period_mode: str = Form(default="single"),
    single_year: str | None = Form(default=None),
    start_year: str | None = Form(default=None),
    end_year: str | None = Form(default=None),
) -> dict[str, str]:
    try:
        academicians = load_active_faculties()
        selected_academicians = _select_academicians(
            academicians,
            set(academician_ids),
        )
        selected_record_types = _validate_record_types(
            set(record_types),
        )
        year_scope = _build_year_scope(
            period_mode=period_mode,
            single_year=single_year,
            start_year=start_year,
            end_year=end_year,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    job = report_jobs.create()

    background_tasks.add_task(
        _run_report_job,
        job.job_id,
        selected_academicians,
        selected_record_types,
        year_scope,
    )

    return {
        "job_id": job.job_id,
        "status_url": str(
            request.url_for(
                "get_report_status",
                job_id=job.job_id,
            )
        ),
    }


@app.get(
    "/reports/{job_id}/status",
    name="get_report_status",
)
def get_report_status(
    request: Request,
    job_id: str,
) -> dict[str, str | int | None]:
    job_status = report_jobs.get_status(job_id)

    if job_status is None:
        raise HTTPException(
            status_code=404,
            detail="Rapor işi bulunamadı.",
        )

    response: dict[str, str | int | None] = {
        "job_id": job_status.job_id,
        "state": job_status.state,
        "message": job_status.message,
        "completed": job_status.completed,
        "total": job_status.total,
        "progress_percent": job_status.progress_percent,
        "error_message": job_status.error_message,
        "download_url": None,
    }

    if job_status.state == "ready":
        response["download_url"] = str(
            request.url_for(
                "download_report",
                job_id=job_id,
            )
        )

    return response


@app.get(
    "/reports/{job_id}/download",
    name="download_report",
)
def download_report(job_id: str):
    download = report_jobs.get_download(job_id)

    if download is None:
        raise HTTPException(
            status_code=409,
            detail="Rapor henüz indirilmeye hazır değil.",
        )

    report_path, download_name = download

    if not report_path.exists():
        report_jobs.remove_and_get_report_path(job_id)

        raise HTTPException(
            status_code=404,
            detail="Rapor dosyası bulunamadı.",
        )

    return FileResponse(
        path=report_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        filename=download_name,
    )


@app.get("/health", tags=["Sistem"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _run_report_job(
    job_id: str,
    academicians: list[Faculty],
    selected_record_types: set[str],
    year_scope: YearScope,
) -> None:
    report_jobs.mark_running(
        job_id,
        "AVESİS kayıt listeleri okunuyor.",
    )

    client = AvesisClient()

    try:
        result = ReportService(client).collect_records(
            academicians=academicians,
            selected_record_types=selected_record_types,
            year_scope=year_scope,
            progress_callback=(
                lambda completed, total, message: (
                    report_jobs.update_progress(
                        job_id,
                        completed=completed,
                        total=total,
                        message=message,
                    )
                )
            ),
        )

        if result.issues:
            report_jobs.mark_failed(
                job_id,
                (
                    "AVESİS'ten bazı kayıtlar okunamadı. "
                    "Lütfen yeniden deneyin."
                ),
            )
            return

        if not result.records:
            report_jobs.mark_failed(
                job_id,
                "Seçiminizle eşleşen kayıt bulunamadı.",
            )
            return

        report_jobs.mark_exporting(job_id)

        report_path = _create_report_path()
        download_name = (
            "deu_avesis_akademik_rapor_"
            f"{datetime.now():%Y-%m-%d_%H-%M}.xlsx"
        )

        ExcelExporter().export(
            records=result.records,
            academicians=academicians,
            selected_record_types=selected_record_types,
            year_scope=year_scope,
            output_path=report_path,
        )

        report_jobs.mark_ready(
            job_id,
            report_path,
            download_name,
        )
    except Exception:
        report_jobs.mark_failed(
            job_id,
            (
                "Rapor oluşturulamadı. "
                "Lütfen kısa süre sonra yeniden deneyin."
            ),
        )
    finally:
        client.close()


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