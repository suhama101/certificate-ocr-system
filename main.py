from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.models.database import init_db

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Certificate OCR System",
    description="Tesseract OCR-based certificate and document processing application.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)


@app.on_event("startup")
def startup_event() -> None:
    init_db()
