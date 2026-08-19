from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.utils.validators import validate_file_size, validate_filename

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    filename = Path(filename).name
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return filename or "document"


async def save_upload(upload: UploadFile) -> tuple[str, str, int]:
    original = safe_filename(upload.filename or "document")
    validate_filename(original)
    content = await upload.read()
    validate_file_size(len(content))

    stored_name = f"{uuid4().hex}_{original}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(content)
    return str(path), original, len(content)
