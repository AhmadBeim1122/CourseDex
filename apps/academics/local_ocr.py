import io

import pytesseract
from django.conf import settings
from PIL import Image

if getattr(settings, "TESSERACT_CMD", ""):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def ocr_image_bytes_locally(image_bytes):
    """Runs local Tesseract OCR on a single image (bytes) and returns text."""
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img).strip()


def ocr_pages_locally(page_images):
    """page_images: list of PNG bytes (one per page). Returns combined text."""
    parts = []
    for i, page_bytes in enumerate(page_images, start=1):
        text = ocr_image_bytes_locally(page_bytes)
        if len(page_images) > 1:
            parts.append(f"--- Page {i} ---\n{text}")
        else:
            parts.append(text)
    return "\n\n".join(parts).strip()