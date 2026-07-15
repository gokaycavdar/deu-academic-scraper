from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.faculty_catalog import load_active_faculties


APP_DIR = Path(__file__).resolve().parent

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
    faculties = load_active_faculties()

    return templates.TemplateResponse(
        request=request,
        name="reports/index.html",
        context={
            "page_title": "Akademik Rapor Oluştur",
            "faculties": faculties,
        },
    )


@app.get("/health", tags=["Sistem"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}