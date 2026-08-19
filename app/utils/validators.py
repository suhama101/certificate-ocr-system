from pathlib import Path

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB


def validate_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed: {allowed}")


def validate_file_size(size: int) -> None:
    if size <= 0:
        raise ValueError("Uploaded file is empty.")
    if size > MAX_FILE_SIZE:
        raise ValueError("File is too large. Maximum size is 15 MB.")
