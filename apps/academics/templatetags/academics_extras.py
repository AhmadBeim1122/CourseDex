import re

from django import template

register = template.Library()

_DRIVE_ID_PATTERNS = [
    re.compile(r"/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"[?&]id=([a-zA-Z0-9_-]+)"),
]


@register.filter
def drive_image_url(url):
    """
    Converts a normal Google Drive share link into a direct, embeddable
    image URL so it works inside an <img> tag. Falls back to the original
    URL untouched if it isn't a recognizable Drive link.
    """
    if not url:
        return url
    for pattern in _DRIVE_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            file_id = match.group(1)
            return f"https://lh3.googleusercontent.com/d/{file_id}=w1000"
    return url



@register.filter
def drive_preview_url(url):
    """
    Converts a Drive share link into an embeddable *preview* URL — works
    for both images and PDFs inside an <iframe>.
    """
    if not url:
        return url
    for pattern in _DRIVE_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"
    return url


@register.filter
def is_pdf_link(url):
    """Best-effort guess of whether a Drive/URL link points to a PDF."""
    if not url:
        return False
    return url.lower().endswith(".pdf") or "pdf" in url.lower()