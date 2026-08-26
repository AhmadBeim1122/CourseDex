# import re

# STOPWORDS = {
#     "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "in", "on",
#     "at", "by", "for", "with", "and", "or", "but", "if", "then", "than", "as", "it", "its", "this",
#     "that", "these", "those", "from", "into", "about", "over", "after", "before", "between",
#     "during", "without", "within", "not", "no", "yes", "do", "does", "did", "done", "has", "have",
#     "had", "having", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
#     "i", "you", "he", "she", "we", "they", "them", "his", "her", "their", "our", "your", "my", "me",
#     "him", "us", "what", "which", "who", "whom", "when", "where", "why", "how", "all", "any",
#     "both", "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "so",
#     "too", "very", "just", "system", "systems", "using", "use", "used", "also", "etc", "one",
#     "two", "three", "part", "parts", "type", "types", "basics", "basic", "introduction",
# }

# WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-']*")
# _TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")


# def _significant_words(title):
#     """Words from a title, minus stopwords and very short filler words."""
#     words = WORD_RE.findall(title or "")
#     out = []
#     for w in words:
#         lw = w.lower()
#         if lw in STOPWORDS or len(lw) < 3:
#             continue
#         out.append(lw)
#     return out


# def build_keyword_index(subject):
#     """
#     {lowercase_word: (kind, id, title)} for every Topic and SubTopic in the
#     given subject. First occurrence wins on collisions.
#     """
#     index = {}
#     topics = list(subject.topics.filter(is_published=True))

#     for topic in topics:
#         for word in _significant_words(topic.title):
#             index.setdefault(word, ("topic", topic.id, topic.title))

#     for topic in topics:
#         for sub in topic.subtopics.all():
#             for word in _significant_words(sub.title):
#                 index.setdefault(word, ("subtopic", sub.id, sub.title))

#     return index


# def link_keywords_in_html(html, keyword_index):
#     """
#     Wraps any word in `html` matching a key in keyword_index with a
#     clickable <a class="kw-link" data-kind data-id>. Only touches plain
#     text — never rewrites anything inside an HTML tag.
#     """
#     if not html or not keyword_index:
#         return html

#     def replace_word(match):
#         word = match.group(0)
#         hit = keyword_index.get(word.lower())
#         if not hit:
#             return word
#         kind, obj_id, _title = hit
#         return (
#             f'<a href="javascript:void(0)" class="kw-link" '
#             f'data-kind="{kind}" data-id="{obj_id}">{word}</a>'
#         )

#     segments = _TAG_SPLIT_RE.split(html)
#     for i, seg in enumerate(segments):
#         if i % 2 == 1:
#             continue  # this segment is an HTML tag — never touch it
#         segments[i] = WORD_RE.sub(replace_word, seg)

#     return "".join(segments)
import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "in", "on",
    "at", "by", "for", "with", "and", "or", "but", "if", "then", "than", "as", "it", "its", "this",
    "that", "these", "those", "from", "into", "about", "over", "after", "before", "between",
    "during", "without", "within", "not", "no", "yes", "do", "does", "did", "done", "has", "have",
    "had", "having", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "i", "you", "he", "she", "we", "they", "them", "his", "her", "their", "our", "your", "my", "me",
    "him", "us", "what", "which", "who", "whom", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "so",
    "too", "very", "just", "system", "systems", "using", "use", "used", "also", "etc", "one",
    "two", "three", "part", "parts", "type", "types", "basics", "basic", "introduction",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-']*")
_TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
_HEADING_OPEN_RE = re.compile(r"^<\s*h[1-6][\s>]", re.IGNORECASE)
_HEADING_CLOSE_RE = re.compile(r"^<\s*/\s*h[1-6]\s*>", re.IGNORECASE)

ACRONYM_MIN_LEN = 2
ACRONYM_MAX_LEN = 5
NORMAL_WORD_MIN_LEN = 4  # normal (non-acronym) words must be at least this long
MAX_LINKS_OUTSIDE_HEADING = 2  # per word, only when no heading match exists at all


def _classify_words(title):
    """
    Returns (normal, acronyms) extracted from a title:
      - normal:   {lowercase_word: original_word}   (case-insensitive matching, len>=4)
      - acronyms: {exact_word: exact_word}           (case-SENSITIVE matching, e.g. 'WAN')
    """
    normal = {}
    acronyms = {}
    for w in WORD_RE.findall(title or ""):
        lw = w.lower()
        if lw in STOPWORDS:
            continue
        if w.isupper() and ACRONYM_MIN_LEN <= len(w) <= ACRONYM_MAX_LEN:
            acronyms[w] = w
        elif len(lw) >= NORMAL_WORD_MIN_LEN:
            normal[lw] = w
    return normal, acronyms


def build_keyword_index(subject):
    """
    Builds a keyword index scoped ONLY to this subject's own Topics and
    SubTopics. Returns:
      {"normal": {lowercase_word: (kind, id, title)},
       "acronyms": {EXACT_word: (kind, id, title)}}
    """
    normal_index = {}
    acronym_index = {}

    def register(kind, obj):
        normal, acronyms = _classify_words(obj.title)
        for lw in normal:
            normal_index.setdefault(lw, (kind, obj.id, obj.title))
        for exact in acronyms:
            acronym_index.setdefault(exact, (kind, obj.id, obj.title))

    topics = list(subject.topics.filter(is_published=True))
    for topic in topics:
        register("topic", topic)
    for topic in topics:
        for sub in topic.subtopics.all():
            register("subtopic", sub)

    return {"normal": normal_index, "acronyms": acronym_index}


def _lookup(word, keyword_index):
    hit = keyword_index["acronyms"].get(word)
    if hit:
        return hit
    return keyword_index["normal"].get(word.lower())


def _dedupe_key(word, hit):
    """Groups occurrences by the matched keyword-object, not by exact casing."""
    kind, obj_id, _title = hit
    return (kind, obj_id)


def link_keywords_in_html(html, keyword_index):
    """
    Wraps matching words with a clickable <a class="kw-link">, using this
    priority per matched Topic/SubTopic:
      1. If the word appears inside a heading (<h1>-<h6>) anywhere in the
         content, link ONLY the occurrence(s) inside heading tags.
      2. Otherwise, link at most MAX_LINKS_OUTSIDE_HEADING occurrences
         anywhere else in the content (first N only).
    Never touches text inside HTML tags themselves.
    """
    if not html or not keyword_index:
        return html

    segments = _TAG_SPLIT_RE.split(html)

    # ---- Pass 1: find which matched keys have at least one heading occurrence ----
    heading_depth = 0
    keys_in_heading = set()
    for seg in segments:
        if not seg:
            continue
        if seg.startswith("<"):
            if _HEADING_OPEN_RE.match(seg):
                heading_depth += 1
            elif _HEADING_CLOSE_RE.match(seg):
                heading_depth = max(0, heading_depth - 1)
            continue
        if heading_depth > 0:
            for m in WORD_RE.finditer(seg):
                hit = _lookup(m.group(0), keyword_index)
                if hit:
                    keys_in_heading.add(_dedupe_key(m.group(0), hit))

    # ---- Pass 2: build output, respecting the priority + occurrence cap ----
    heading_depth = 0
    outside_link_counts = {}
    out_segments = []

    for seg in segments:
        if not seg:
            continue
        if seg.startswith("<"):
            if _HEADING_OPEN_RE.match(seg):
                heading_depth += 1
            elif _HEADING_CLOSE_RE.match(seg):
                heading_depth = max(0, heading_depth - 1)
            out_segments.append(seg)
            continue

        in_heading = heading_depth > 0

        def replace_word(match):
            word = match.group(0)
            hit = _lookup(word, keyword_index)
            if not hit:
                return word
            key = _dedupe_key(word, hit)
            has_heading_match = key in keys_in_heading

            if has_heading_match and not in_heading:
                return word  # heading match exists elsewhere — skip this non-heading occurrence

            if not has_heading_match:
                # no heading occurrence anywhere — allow only first N occurrences total
                count = outside_link_counts.get(key, 0)
                if count >= MAX_LINKS_OUTSIDE_HEADING:
                    return word
                outside_link_counts[key] = count + 1

            kind, obj_id, _title = hit
            return (
                f'<a href="javascript:void(0)" class="kw-link" '
                f'data-kind="{kind}" data-id="{obj_id}">{word}</a>'
            )

        out_segments.append(WORD_RE.sub(replace_word, seg))

    return "".join(out_segments)