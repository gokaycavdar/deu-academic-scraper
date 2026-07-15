from pathlib import Path

from app.services.report_job_store import ReportJobStore


def test_progress_status_is_calculated() -> None:
    store = ReportJobStore()
    job = store.create()

    store.update_progress(
        job.job_id,
        completed=3,
        total=8,
        message="3 kayıt işlendi.",
    )

    status = store.get_status(job.job_id)

    assert status is not None
    assert status.state == "running"
    assert status.completed == 3
    assert status.total == 8
    assert status.progress_percent == 38


def test_ready_job_exposes_download_information() -> None:
    store = ReportJobStore()
    job = store.create()
    report_path = Path("data/generated/web/test_raporu.xlsx")

    store.mark_ready(
        job.job_id,
        report_path,
        "test_raporu.xlsx",
    )

    assert store.get_download(job.job_id) == (
        report_path,
        "test_raporu.xlsx",
    )


def test_failed_job_keeps_user_message() -> None:
    store = ReportJobStore()
    job = store.create()

    store.mark_failed(
        job.job_id,
        "Seçiminizle eşleşen kayıt bulunamadı.",
    )

    status = store.get_status(job.job_id)

    assert status is not None
    assert status.state == "failed"
    assert status.error_message == (
        "Seçiminizle eşleşen kayıt bulunamadı."
    )