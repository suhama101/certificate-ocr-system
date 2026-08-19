from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = image.convert("RGB")
    arr = np.array(rgb)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def crop_white_margins(image: Image.Image) -> Image.Image:
    """
    Remove large white margins around the actual certificate.
    This helps OCR when the certificate occupies only a small
    portion of the uploaded image.
    """
    img = pil_to_bgr(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect pixels that are not almost white
    mask = (gray < 245).astype(np.uint8) * 255

    coords = cv2.findNonZero(mask)

    if coords is None:
        return image

    x, y, w, h = cv2.boundingRect(coords)

    # Keep a little padding around the certificate
    padding = max(20, int(max(w, h) * 0.03))

    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.width, x + w + padding)
    y2 = min(image.height, y + h + padding)

    return image.crop((x1, y1, x2, y2))


def deskew(binary: np.ndarray) -> np.ndarray:
    """
    Correct slightly tilted certificate images.
    """
    coords = np.column_stack(np.where(binary < 255))

    if coords.size == 0:
        return binary

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Ignore extremely small rotations
    if abs(angle) < 0.2:
        return binary

    h, w = binary.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0,
    )

    return cv2.warpAffine(
        binary,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Improve certificate readability before sending it to Tesseract OCR.

    Pipeline:
    1. Crop large white margins
    2. Convert to grayscale
    3. Upscale small certificates
    4. Improve contrast
    5. Remove noise
    6. Adaptive thresholding
    7. Deskew image
    """

    # Step 1: Remove unnecessary white space
    image = crop_white_margins(image)

    # Step 2: Convert PIL image to OpenCV format
    img = pil_to_bgr(image)

    # Step 3: Convert to grayscale
    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY,
    )

    # Step 4: Upscale certificate so small text becomes readable
    h, w = gray.shape[:2]

    if max(h, w) < 2200:
        scale = 2200 / max(h, w)

        gray = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

    # Step 5: Improve local contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(gray)

    # Step 6: Remove image noise
    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        h=7,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    # Step 7: Convert to high-contrast black and white image
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        41,
        11,
    )

    # Step 8: Correct image rotation
    rotated = deskew(binary)

    return Image.fromarray(rotated)