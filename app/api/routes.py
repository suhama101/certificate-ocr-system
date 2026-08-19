from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.extractor import parse_certificate_fields
from app.core.ocr_engine import OCRConfigurationError, extract_text_from_document
from app.models.database import delete_document, get_document, list_documents, save_document
from app.utils.file_handler import save_upload

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def public_record(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "stored_path"}


async def process_upload(file: UploadFile) -> dict:
    path = None
    try:
        path, original_name, _ = await save_upload(file)
        raw_text, page_count, confidence = extract_text_from_document(path)
        fields = parse_certificate_fields(raw_text)
        record = {
            "id": uuid4().hex[:12],
            "filename": original_name,
            "page_count": page_count,
            "average_confidence": confidence,
            "fields": fields.model_dump(),
            "raw_text": raw_text,
            "stored_path": path,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        save_document(record)
        return record
    except (ValueError, OCRConfigurationError) as exc:
        if path and os.path.exists(path):
            os.remove(path)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        if path and os.path.exists(path):
            os.remove(path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
   return templates.TemplateResponse(request, "index.html")


@router.get("/health")
async def health():
    return {"status": "ok", "service": "Certificate OCR System"}


@router.post("/upload")
async def upload_certificate(file: UploadFile = File(...)):
    record = await process_upload(file)
    return JSONResponse(public_record(record))


@router.post("/extract")
async def extract_certificate(file: UploadFile = File(...)):
    record = await process_upload(file)
    return JSONResponse(public_record(record))


@router.get("/results")
async def recent_results(limit: int = 20):
    return [public_record(item) for item in list_documents(max(1, min(limit, 100)))]


@router.get("/results/{document_id}")
async def get_results(document_id: str):
    record = get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return public_record(record)


@router.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    stored_path = delete_document(document_id)
    if stored_path is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError:
            pass
    return {"deleted": True, "id": document_id}


@router.get("/results/{document_id}/json")
async def download_json(document_id: str):
    record = get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    payload = json.dumps(public_record(record), indent=2, ensure_ascii=False)
    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{document_id}.json"'},
    )


@router.get("/results/{document_id}/csv")
async def download_csv(document_id: str):
    record = get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Field", "Value"])
    for key, value in record["fields"].items():
        writer.writerow([key, json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value or ""])
    writer.writerow(["average_confidence", record.get("average_confidence") or ""])
    writer.writerow(["filename", record["filename"]])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{document_id}.csv"'},
    )
