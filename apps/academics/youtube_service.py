import requests
from django.conf import settings

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_youtube_videos(query, language_code, max_results=2):
    """
    Searches YouTube via the official YouTube Data API v3 (free tier,
    10,000 units/day; each search call costs 100 units).
    language_code: 'en' or 'hi' — biases results toward that language.
    Returns a list of {"video_id", "title"} dicts.
    """
    key = settings.YOUTUBE_API_KEY
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY not set in .env")

    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "q": query,
        "relevanceLanguage": language_code,
        "safeSearch": "strict",
        "videoEmbeddable": "true",
        "key": key,
    }
    r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=20)
    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"HTTP {r.status_code} — {detail}"[:500])

    items = r.json().get("items", [])
    results = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        title = item.get("snippet", {}).get("title", "")
        if video_id:
            results.append({"video_id": video_id, "title": title})
    return results


def suggest_videos_for_title(title):
    """
    Returns up to 4 suggestions for a Topic/SubTopic title:
    2 English + 2 Hindi, each as {"video_id", "title", "language"}.
    Any language's search failing doesn't block the other.
    """
    suggestions = []
    for lang, label in (("en", "English"), ("hi", "Hindi")):
        try:
            results = search_youtube_videos(title, lang, max_results=2)
        except Exception:
            results = []
        for r in results:
            suggestions.append({
                "video_id": r["video_id"],
                "title": r["title"],
                "language": label,
            })
    return suggestions