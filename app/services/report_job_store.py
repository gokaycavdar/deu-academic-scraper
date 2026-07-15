from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class ReportJobStatus:
    job_id: str
    state: str
    message: str
    completed: int
    total: int | None
    progress_percent: int | None
    error_message: str | None


@dataclass
class _ReportJob:
    job_id: str
    state: str = "queued"
    message: str = "Rapor kuyruğa alındı."
    completed: int = 0
    total: int | None = None
    report_path: Path | None = None
    download_name: str | None = None
    error_message: str | None = None


class ReportJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, _ReportJob] = {}
        self._lock = Lock()

    def create(self) -> ReportJobStatus:
        job = _ReportJob(job_id=uuid4().hex)

        with self._lock:
            self._jobs[job.job_id] = job

        return self._to_status(job)

    def get_status(self, job_id: str) -> ReportJobStatus | None:
        with self._lock:
            job = self._jobs.get(job_id)

            if job is None:
                return None

            return self._to_status(job)

    def mark_running(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._get_job(job_id)

            if job is None:
                return

            job.state = "running"
            job.message = message

    def update_progress(
        self,
        job_id: str,
        *,
        completed: int,
        total: int | None,
        message: str,
    ) -> None:
        with self._lock:
            job = self._get_job(job_id)

            if job is None:
                return

            job.state = "running"
            job.completed = completed
            job.total = total
            job.message = message

    def mark_exporting(self, job_id: str) -> None:
        with self._lock:
            job = self._get_job(job_id)

            if job is None:
                return

            job.state = "exporting"
            job.message = "Excel dosyası hazırlanıyor."

    def mark_ready(
        self,
        job_id: str,
        report_path: Path,
        download_name: str,
    ) -> None:
        with self._lock:
            job = self._get_job(job_id)

            if job is None:
                return

            job.state = "ready"
            job.message = "Rapor hazır. İndirme başlatılıyor."
            job.completed = job.total or job.completed
            job.report_path = report_path
            job.download_name = download_name

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> None:
        with self._lock:
            job = self._get_job(job_id)

            if job is None:
                return

            job.state = "failed"
            job.message = "Rapor oluşturulamadı."
            job.error_message = error_message

    def get_download(
        self,
        job_id: str,
    ) -> tuple[Path, str] | None:
        with self._lock:
            job = self._jobs.get(job_id)

            if (
                job is None
                or job.state != "ready"
                or job.report_path is None
                or job.download_name is None
            ):
                return None

            return job.report_path, job.download_name

    def remove_and_get_report_path(
        self,
        job_id: str,
    ) -> Path | None:
        with self._lock:
            job = self._jobs.pop(job_id, None)

        if job is None:
            return None

        return job.report_path

    
    def _get_job(self, job_id: str) -> _ReportJob | None:
        return self._jobs.get(job_id)

    @staticmethod
    def _to_status(job: _ReportJob) -> ReportJobStatus:
        progress_percent = None

        if job.total is not None and job.total > 0:
            progress_percent = round(
                (job.completed / job.total) * 100
            )

        return ReportJobStatus(
            job_id=job.job_id,
            state=job.state,
            message=job.message,
            completed=job.completed,
            total=job.total,
            progress_percent=progress_percent,
            error_message=job.error_message,
        )