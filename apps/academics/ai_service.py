import base64
import re
import time
from datetime import date

import io

import pymupdf as fitz  # PyMuPDF (new import name; kept as `fitz` alias below for minimal changes)
import requests
from django.conf import settings
from PIL import Image

from .local_ocr import ocr_image_bytes_locally, ocr_pages_locally

PROVIDERS = {
    "groq": {"label": "API 1 · Groq", "daily_limit": 14400},
    "gemini": {"label": "API 2 · Gemini", "daily_limit": 250},
    "openrouter": {"label": "API 3 · OpenRouter", "daily_limit": 50},
    "ollama": {"label": "API 4 · Ollama Cloud", "daily_limit": None},
}

PROMPT_TEMPLATE = (
    "You are writing study notes for a university student. Write a clear, "
    "well-structured explanation (150-300 words) of the following topic. "
    "Format the answer as clean HTML using ONLY these tags where useful: "
    "<p>, <h3>, <strong>, <em>, <blockquote>, <ul>, <li>, <ol>, <dl>, <dt>, "
    "<dd> (use <dl>/<dt>/<dd> for any key term + definition pairs). Do not "
    "include <html>, <head>, <body>, markdown syntax, or code fences — "
    "return just the HTML fragment itself. Topic: \"{title}\"."
)

SOLUTION_PROMPT_TEMPLATE = (
    "You are an expert university teacher preparing an exam solution key. "
    "Below is text extracted (via OCR) from a scanned exam question paper — "
    "it may contain minor OCR errors; correct obvious ones silently.\n\n"
    "Go through EVERY question in order. Judge each question's expected "
    "length from its marks/instructions/phrasing:\n"
    "- Short questions (define, MCQ, fill-in-the-blank, 'briefly', low marks): "
    "give a concise, focused answer (2-6 sentences).\n"
    "- Long questions ('explain in detail', 'discuss', 'describe', high marks): "
    "give a thorough, well-organized answer with sub-points where useful.\n\n"
    "Format the ENTIRE response as clean HTML using ONLY these tags: <h3> "
    "(for each question number/heading), <p>, <strong>, <em>, <blockquote>, "
    "<ul>, <li>, <ol>, <dl>, <dt>, <dd>. Do not include <html>, <head>, "
    "<body>, markdown syntax, or code fences — return just the HTML "
    "fragment itself.\n\nQuestion paper text:\n\n{paper_text}"
)

OCR_PROMPT = (
    "Extract ALL text from this exam question paper image exactly as "
    "written, preserving question numbers, sub-parts, marks, and line "
    "breaks as closely as possible. Return plain text only — no "
    "commentary, no markdown, no code fences."
)

RETRYABLE_STATUS = (429, 503)
MAX_RETRIES_PER_MODEL = 3
RETRY_DELAY_SECONDS = 3

_DRIVE_ID_PATTERNS = [
    re.compile(r"/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"[?&]id=([a-zA-Z0-9_-]+)"),
]


def drive_direct_image_url(url):
    """Same conversion used by the frontend `drive_image_url` template filter."""
    if not url:
        return url
    for pattern in _DRIVE_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            file_id = match.group(1)
            return f"https://lh3.googleusercontent.com/d/{file_id}=w2000"
    return url


def _extract_drive_file_id(url):
    for pattern in _DRIVE_ID_PATTERNS:
        match = pattern.search(url or "")
        if match:
            return match.group(1)
    return None


def _download_drive_file(drive_link):
    """
    Downloads the raw bytes behind a Google Drive share link (works for
    images and PDFs, as long as the file is shared as 'Anyone with the
    link' and is small enough to skip Drive's virus-scan interstitial).
    Returns (bytes, content_type).
    """
    file_id = _extract_drive_file_id(drive_link)
    if not file_id:
        raise RuntimeError("Couldn't find a Google Drive file ID in that link.")

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resp = requests.get(url, timeout=settings.OCR_TIMEOUT_SECONDS, allow_redirects=True)
    if resp.status_code != 200:
        raise RuntimeError(f"Could not download the file (HTTP {resp.status_code}).")

    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()

    if content_type == "text/html":
        raise RuntimeError(
            "Drive returned a confirmation page instead of the file — this "
            "usually happens with large files or restricted sharing. Make "
            "sure the file is shared as 'Anyone with the link' and under ~25MB."
        )

    return resp.content, content_type


def _pdf_to_page_images(pdf_bytes, max_pages=6, zoom=2.0):
    """Renders up to max_pages pages of a PDF to PNG bytes using PyMuPDF."""
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        matrix = fitz.Matrix(zoom, zoom)
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(matrix=matrix)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def _gemini_vision_ocr(image_parts):
    """image_parts: list of (bytes, mime_type). Returns transcribed text."""
    key = settings.GEMINI_API_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")

    models = _model_list(settings.GEMINI_MODEL)
    if not models:
        raise RuntimeError("No models configured for gemini — check GEMINI_MODEL in .env")

    parts = [{"text": OCR_PROMPT}]
    for data, mime in image_parts:
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})

    errors = []
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            r = _post_with_retry(url, headers={}, json_body={"contents": [{"parts": parts}]}, timeout=settings.OCR_TIMEOUT_SECONDS)
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            errors.append(f"[{model}] {e}")
            continue

    raise RuntimeError("\n".join(errors)[:800])


def _prepare_drive_pages(drive_link):
    """
    Downloads the Drive file and returns raw page images (PNG/original
    bytes) plus their mime types — shared prep step for both OCR methods.
    Returns (page_images, image_parts) where image_parts is
    [(bytes, mime_type), ...] ready for Gemini, and page_images is a plain
    list of image bytes ready for local OCR.

    Google Drive sometimes reports a generic 'application/octet-stream'
    Content-Type instead of 'application/pdf' or 'image/...', so instead
    of trusting the header we sniff the actual bytes: try parsing as a
    PDF first, then fall back to validating it as an image.
    """
    file_bytes, content_type = _download_drive_file(drive_link)
    looks_like_pdf = content_type == "application/pdf" or drive_link.lower().endswith(".pdf")

    # 1) Try as PDF (either the header/URL says so, or the type is ambiguous).
    if looks_like_pdf or content_type in ("", "application/octet-stream"):
        try:
            page_images = _pdf_to_page_images(file_bytes)
            if page_images:
                return page_images, [(img, "image/png") for img in page_images]
        except Exception:
            pass  # not actually a valid PDF — fall through to image handling

    # 2) Try as an image (either the header says so, or the type is ambiguous).
    if content_type.startswith("image/") or content_type in ("", "application/octet-stream"):
        try:
            Image.open(io.BytesIO(file_bytes)).verify()
            mime = content_type if content_type.startswith("image/") else "image/jpeg"
            return [file_bytes], [(file_bytes, mime)]
        except Exception:
            pass

    raise RuntimeError(
        f"Couldn't recognize this file as a PDF or image (Content-Type was "
        f"'{content_type or 'unknown'}'). Make sure the Drive file is "
        "shared as 'Anyone with the link' and is a real PDF or image file."
    )


def ocr_extract_text_gemini(drive_link):
    """Extracts text using Gemini's vision model only (no fallback)."""
    _page_images, image_parts = _prepare_drive_pages(drive_link)
    return _gemini_vision_ocr(image_parts)


def ocr_extract_text_tesseract(drive_link):
    """Extracts text using local Tesseract OCR only (no Gemini call)."""
    page_images, _image_parts = _prepare_drive_pages(drive_link)
    text = ocr_pages_locally(page_images)
    if not text:
        raise RuntimeError(
            "Tesseract returned empty text. Make sure Tesseract is "
            "installed and TESSERACT_CMD is set correctly in .env, and "
            "that the source image/PDF is clear enough to read."
        )
    return text


def _model_list(raw):
    return [m.strip() for m in (raw or "").split(",") if m.strip()]


def _describe_error(r):
    try:
        return r.json()
    except Exception:
        return r.text


def _post_with_retry(url, headers, json_body, timeout=45):
    last_error = None
    for attempt in range(MAX_RETRIES_PER_MODEL + 1):
        r = requests.post(url, headers=headers, json=json_body, timeout=timeout)
        if r.status_code == 200:
            return r
        last_error = r
        if r.status_code in RETRYABLE_STATUS and attempt < MAX_RETRIES_PER_MODEL:
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
            continue
        break
    raise RuntimeError(f"HTTP {last_error.status_code} — {_describe_error(last_error)}"[:600])


def _call_groq_model(model, prompt):
    key = settings.GROQ_API_KEY
    if not key:
        raise RuntimeError("GROQ_API_KEY not set in .env")
    r = _post_with_retry(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json_body={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.5},
    )
    return r.json()["choices"][0]["message"]["content"].strip()


def _call_gemini_model(model, prompt):
    key = settings.GEMINI_API_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r = _post_with_retry(url, headers={}, json_body={"contents": [{"parts": [{"text": prompt}]}]})
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openrouter_model(model, prompt):
    key = settings.OPENROUTER_API_KEY
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")
    r = _post_with_retry(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json_body={"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    return r.json()["choices"][0]["message"]["content"].strip()


def _call_ollama_model(model, prompt):
    key = settings.OLLAMA_API_KEY
    if not key:
        raise RuntimeError("OLLAMA_API_KEY not set in .env")
    r = _post_with_retry(
        "https://ollama.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json_body={"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    return r.json()["choices"][0]["message"]["content"].strip()


PROVIDER_CONFIG = {
    "groq": {"model_setting": "GROQ_MODEL", "caller": _call_groq_model},
    "gemini": {"model_setting": "GEMINI_MODEL", "caller": _call_gemini_model},
    "openrouter": {"model_setting": "OPENROUTER_MODEL", "caller": _call_openrouter_model},
    "ollama": {"model_setting": "OLLAMA_MODEL", "caller": _call_ollama_model},
}


def _run_provider(provider, prompt):
    if provider not in PROVIDERS:
        raise ValueError("Unknown provider")
    cfg = PROVIDER_CONFIG[provider]
    models = _model_list(getattr(settings, cfg["model_setting"], ""))
    if not models:
        raise RuntimeError(f"No models configured for {provider} — check {cfg['model_setting']} in .env")

    errors = []
    for model in models:
        try:
            return cfg["caller"](model, prompt)
        except Exception as e:
            errors.append(f"[{model}] {e}")
            continue

    joined = "\n".join(errors)
    raise RuntimeError(f"All {len(models)} fallback model(s) failed for {provider}:\n{joined}"[:800])


def generate_explanation(provider, title):
    return _run_provider(provider, PROMPT_TEMPLATE.format(title=title))


def generate_solution(provider, paper_text):
    return _run_provider(provider, SOLUTION_PROMPT_TEMPLATE.format(paper_text=paper_text[:8000]))



def log_usage(provider):
    from .models import AIProviderUsage
    obj, _ = AIProviderUsage.objects.get_or_create(provider=provider, date=date.today())
    obj.count += 1
    obj.save(update_fields=["count"])


def get_usage_summary():
    from .models import AIProviderUsage
    today = date.today()
    summary = []
    for key, info in PROVIDERS.items():
        row = AIProviderUsage.objects.filter(provider=key, date=today).first()
        used = row.count if row else 0
        limit = info["daily_limit"]
        summary.append({
            "key": key,
            "label": info["label"],
            "used": used,
            "limit": limit if limit is not None else "—",
            "remaining": "—" if limit is None else max(limit - used, 0),
        })
    return summary