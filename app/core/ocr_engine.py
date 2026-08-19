from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import pytesseract
from PIL import Image, ImageOps
from pdf2image import convert_from_path
from pytesseract import Output

from app.core.preprocessor import (
    preprocess_image,
    crop_white_margins,
)


class OCRConfigurationError(RuntimeError):
    pass


def configure_tesseract() -> None:
    custom = os.getenv("TESSERACT_CMD")

    if custom:
        pytesseract.pytesseract.tesseract_cmd = custom


def load_document_pages(
    file_path: str | Path,
) -> List[Image.Image]:

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":

        poppler_path = os.getenv("POPPLER_PATH") or None

        try:
            return convert_from_path(
                str(path),
                dpi=300,
                poppler_path=poppler_path,
            )

        except Exception as exc:
            raise OCRConfigurationError(
                "PDF conversion failed. Install Poppler and add it "
                "to PATH, or set POPPLER_PATH."
            ) from exc

    try:
        return [
            Image.open(path).convert("RGB")
        ]

    except Exception as exc:
        raise ValueError(
            f"Unable to read image file: {exc}"
        ) from exc


def upscale_image(
    image: Image.Image,
    target_size: int = 2400,
) -> Image.Image:

    width, height = image.size
    largest = max(width, height)

    if largest >= target_size:
        return image

    scale = target_size / largest

    new_width = int(width * scale)
    new_height = int(height * scale)

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )


def run_tesseract(
    image: Image.Image,
    psm: int,
) -> Tuple[str, float | None]:

    config = f"--oem 3 --psm {psm}"

    text = pytesseract.image_to_string(
        image,
        config=config,
    )

    data = pytesseract.image_to_data(
        image,
        config=config,
        output_type=Output.DICT,
    )

    confidences = []

    for value in data.get("conf", []):

        try:
            score = float(value)

            if score >= 0:
                confidences.append(score)

        except (TypeError, ValueError):
            continue

    average = (
        round(
            sum(confidences) / len(confidences),
            2,
        )
        if confidences
        else None
    )

    return text.strip(), average


def text_quality_score(
    text: str,
    confidence: float | None,
) -> float:

    score = confidence or 0

    lower = text.lower()

    important_words = [
        "certificate",
        "presented",
        "participation",
        "completion",
        "achievement",
        "organization",
        "university",
        "institute",
        "alliance",
        "dated",
    ]

    for word in important_words:
        if word in lower:
            score += 2

    # Reward useful OCR text length
    score += min(
        len(text) / 100,
        10,
    )

    # Reward certificate ID style patterns
    import re

    if re.search(
        r"\b[A-Z]{2,15}-\d{2,4}-[A-Z0-9\-]{2,}\b",
        text,
        re.IGNORECASE,
    ):
        score += 8

    return score


def ocr_page(
    image: Image.Image,
) -> Tuple[str, float | None]:

    configure_tesseract()

    try:

        candidates = []

        # -------------------------------------------------
        # Candidate 1:
        # Original certificate with white margins removed.
        # Best for clean digital certificates and names.
        # -------------------------------------------------

        cropped = crop_white_margins(image)
        cropped = upscale_image(
            cropped,
            target_size=2400,
        )

        text1, confidence1 = run_tesseract(
            cropped,
            psm=3,
        )

        candidates.append(
            (
                text1,
                confidence1,
                text_quality_score(
                    text1,
                    confidence1,
                ),
            )
        )

        # -------------------------------------------------
        # Candidate 2:
        # Grayscale + auto contrast.
        # Useful for light text and scanned certificates.
        # -------------------------------------------------

        grayscale = ImageOps.grayscale(cropped)
        grayscale = ImageOps.autocontrast(
            grayscale,
        )

        text2, confidence2 = run_tesseract(
            grayscale,
            psm=3,
        )

        candidates.append(
            (
                text2,
                confidence2,
                text_quality_score(
                    text2,
                    confidence2,
                ),
            )
        )

        # -------------------------------------------------
        # Candidate 3:
        # Full preprocessing pipeline.
        # Useful for noisy or low-quality documents.
        # -------------------------------------------------

        processed = preprocess_image(image)

        text3, confidence3 = run_tesseract(
            processed,
            psm=6,
        )

        candidates.append(
            (
                text3,
                confidence3,
                text_quality_score(
                    text3,
                    confidence3,
                ),
            )
        )

        # -------------------------------------------------
        # Candidate 4:
        # Sparse-text mode for unusual layouts.
        # -------------------------------------------------

        text4, confidence4 = run_tesseract(
            cropped,
            psm=11,
        )

        candidates.append(
            (
                text4,
                confidence4,
                text_quality_score(
                    text4,
                    confidence4,
                ),
            )
        )

        # Select the best OCR result automatically
        best_text, best_confidence, _ = max(
            candidates,
            key=lambda item: item[2],
        )

        return (
            best_text,
            best_confidence,
        )

    except pytesseract.TesseractNotFoundError as exc:

        raise OCRConfigurationError(
            "Tesseract OCR was not found. "
            "Install Tesseract and add it to PATH, "
            "or set TESSERACT_CMD."
        ) from exc


def extract_text_from_document(
    file_path: str | Path,
) -> tuple[str, int, float | None]:

    pages = load_document_pages(
        file_path
    )

    page_texts: list[str] = []
    page_confidences: list[float] = []

    for index, page in enumerate(
        pages,
        start=1,
    ):

        text, confidence = ocr_page(
            page
        )

        page_texts.append(
            f"--- Page {index} ---\n{text}"
        )

        if confidence is not None:
            page_confidences.append(
                confidence
            )

    avg_confidence = (
        round(
            sum(page_confidences)
            / len(page_confidences),
            2,
        )
        if page_confidences
        else None
    )

    return (
        "\n\n".join(page_texts).strip(),
        len(pages),
        avg_confidence,
    )