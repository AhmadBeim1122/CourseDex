from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render

from .keyword_linker import build_keyword_index, link_keywords_in_html
from .models import PastPaper, Program, Semester, Subject, SubTopic, Topic

TOPIC_BROWSE_PAGE_SIZE = 24


def _get_program(program_slug):
    return get_object_or_404(Program.published, slug=program_slug)


def _get_semester(program, semester_number):
    return get_object_or_404(
        Semester.published, program=program, number=semester_number
    )


def _get_subject(semester, subject_slug):
    return get_object_or_404(Subject.published, semester=semester, slug=subject_slug)


# ---------------------------------------------------------------------------
# Courses (study material) browsing:
#   /courses/                                        -> programs
#   /courses/<program>/                               -> semesters
#   /courses/<program>/<semester>/                    -> subjects
#   /courses/<program>/<semester>/<subject>/          -> topic outline
#   /courses/<program>/<semester>/<subject>/<topic>/  -> topic detail
# ---------------------------------------------------------------------------
def program_list(request):
    q = request.GET.get("q", "").strip()
    programs = Program.published.all()
    if q:
        programs = programs.filter(
            Q(name__icontains=q) | Q(short_name__icontains=q)
        )
    context = {"programs": programs, "query": q, "page_title": "Courses"}
    template = "academics/program_list.html"
    if request.htmx:
        template = "partials/program_grid.html"
    return render(request, template, context)


def semester_list(request, program_slug):
    program = _get_program(program_slug)
    semesters = program.semesters.filter(is_published=True).prefetch_related(
        Prefetch("subjects", queryset=Subject.published.all())
    )
    context = {
        "program": program,
        "semesters": semesters,
        "page_title": f"{program.short_name} — Semesters & Subjects",
        "mode": "courses",
    }
    return render(request, "academics/semester_list.html", context)


def subject_list(request, program_slug, semester_number):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subjects = semester.subjects.filter(is_published=True)
    context = {
        "program": program,
        "semester": semester,
        "subjects": subjects,
        "page_title": f"{program.short_name} {semester.display_name} — Subjects",
        "mode": "courses",
    }
    template = "academics/subject_list.html"
    if request.htmx:
        template = "partials/subject_grid.html"
    return render(request, template, context)


def topic_list(request, program_slug, semester_number, subject_slug):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subject = _get_subject(semester, subject_slug)
    topics = subject.topics.filter(is_published=True)
    context = {
        "program": program,
        "semester": semester,
        "subject": subject,
        "topics": topics,
        "page_title": f"{subject.name} — Outline",
    }
    return render(request, "academics/topic_list.html", context)


def topic_detail(request, program_slug, semester_number, subject_slug, topic_slug):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subject = _get_subject(semester, subject_slug)
    topic = get_object_or_404(
        Topic.published, subject=subject, slug=topic_slug
    )
    topics = list(subject.topics.filter(is_published=True))
    ids = [t.id for t in topics]
    idx = ids.index(topic.id) if topic.id in ids else -1
    prev_topic = topics[idx - 1] if idx > 0 else None
    next_topic = topics[idx + 1] if 0 <= idx < len(topics) - 1 else None

    context = {
        "program": program,
        "semester": semester,
        "subject": subject,
        "topic": topic,
        "topics": topics,
        "prev_topic": prev_topic,
        "next_topic": next_topic,
        "images": topic.images.all(),
        "subject_past_papers": subject.past_papers.filter(is_published=True).order_by("-year"),
        "page_title": topic.title,
    }
    return render(request, "academics/topic_detail.html", context)

def subtopic_detail(request, program_slug, semester_number, subject_slug, topic_slug, subtopic_slug):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subject = _get_subject(semester, subject_slug)
    topic = get_object_or_404(Topic.published, subject=subject, slug=topic_slug)
    subtopic = get_object_or_404(SubTopic, topic=topic, slug=subtopic_slug)

    siblings = list(topic.subtopics.all())
    ids = [s.id for s in siblings]
    idx = ids.index(subtopic.id) if subtopic.id in ids else -1
    prev_subtopic = siblings[idx - 1] if idx > 0 else None
    next_subtopic = siblings[idx + 1] if 0 <= idx < len(siblings) - 1 else None

    context = {
        "program": program,
        "semester": semester,
        "subject": subject,
        "topic": topic,
        "subtopic": subtopic,
        "prev_subtopic": prev_subtopic,
        "next_subtopic": next_subtopic,
        "page_title": subtopic.title,
        "subject_past_papers": subject.past_papers.filter(is_published=True).order_by("-year"),
    }
    return render(request, "academics/subtopic_detail.html", context)

# ---------------------------------------------------------------------------
# Past Papers browsing:
#   /past-papers/                                       -> programs
#   /past-papers/<program>/                              -> semesters
#   /past-papers/<program>/<semester>/                   -> subjects
#   /past-papers/<program>/<semester>/<subject>/         -> years available
#   /past-papers/<program>/<semester>/<subject>/<year>/  -> papers for that year
# ---------------------------------------------------------------------------
def pastpaper_program_list(request):
    q = request.GET.get("q", "").strip()
    programs = Program.published.all()
    if q:
        programs = programs.filter(
            Q(name__icontains=q) | Q(short_name__icontains=q)
        )
    context = {
        "programs": programs,
        "query": q,
        "page_title": "Past Papers",
        "mode": "pastpapers",
    }
    template = "academics/pastpaper_program_list.html"
    if request.htmx:
        template = "partials/program_grid.html"
    return render(request, template, context)


def pastpaper_semester_list(request, program_slug):
    program = _get_program(program_slug)
    semesters = program.semesters.filter(is_published=True).prefetch_related(
        Prefetch("subjects", queryset=Subject.published.all())
    )
    context = {
        "program": program,
        "semesters": semesters,
        "page_title": f"{program.short_name} — Past Papers",
        "mode": "pastpapers",
    }
    return render(request, "academics/semester_list.html", context)


def pastpaper_subject_list(request, program_slug, semester_number):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subjects = semester.subjects.filter(is_published=True)
    context = {
        "program": program,
        "semester": semester,
        "subjects": subjects,
        "page_title": f"{program.short_name} {semester.display_name} — Past Papers",
        "mode": "pastpapers",
    }
    template = "academics/subject_list.html"
    if request.htmx:
        template = "partials/subject_grid.html"
    return render(request, template, context)


def pastpaper_year_list(request, program_slug, semester_number, subject_slug):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subject = _get_subject(semester, subject_slug)
    years = subject.past_paper_years  # only years that actually have papers
    context = {
        "program": program,
        "semester": semester,
        "subject": subject,
        "years": years,
        "page_title": f"{subject.name} — Past Papers",
    }
    return render(request, "academics/pastpaper_year_list.html", context)





def pastpaper_detail(request, program_slug, semester_number, subject_slug, year):
    program = _get_program(program_slug)
    semester = _get_semester(program, semester_number)
    subject = _get_subject(semester, subject_slug)
    papers = list(PastPaper.published.filter(subject=subject, year=year))
    if not papers:
        raise Http404("No past papers found for this year.")

    keyword_index = build_keyword_index(subject)
    for paper in papers:
        if paper.solution_type == PastPaper.SolutionType.TEXT and paper.solution_text:
            paper.linked_solution_html = link_keywords_in_html(paper.solution_text, keyword_index)
        else:
            paper.linked_solution_html = paper.solution_text

    outline_topics = subject.topics.filter(is_published=True).prefetch_related("subtopics")

    context = {
        "program": program,
        "semester": semester,
        "subject": subject,
        "year": year,
        "papers": papers,
        "outline_topics": outline_topics,
        "page_title": f"{subject.name} — {year} Past Papers",
    }
    return render(request, "academics/pastpaper_detail.html", context)


def keyword_content_api(request, kind, pk):
    """Returns a Topic's or SubTopic's title/content as JSON, for the modal."""
    if kind == "topic":
        obj = get_object_or_404(Topic.published, pk=pk)
    elif kind == "subtopic":
        obj = get_object_or_404(SubTopic, pk=pk)
    else:
        return JsonResponse({"ok": False, "error": "Unknown content type."}, status=404)

    return JsonResponse({
        "ok": True,
        "title": obj.title,
        "content": obj.content,
        "url": obj.get_absolute_url(),
    })



# ---------------------------------------------------------------------------
# Browse Topics — searchable gallery of every Topic + SubTopic, site-wide
# ---------------------------------------------------------------------------
def _collect_browse_items(q):
    topics_qs = (
        Topic.published.filter(
            subject__is_published=True,
            subject__semester__is_published=True,
            subject__semester__program__is_published=True,
        )
        .select_related("subject", "subject__semester", "subject__semester__program")
        .prefetch_related("videos", "images", "documents")
    )
    subtopics_qs = (
        SubTopic.objects.filter(
            topic__is_published=True,
            topic__subject__is_published=True,
            topic__subject__semester__is_published=True,
            topic__subject__semester__program__is_published=True,
        )
        .select_related(
            "topic", "topic__subject", "topic__subject__semester",
            "topic__subject__semester__program",
        )
        .prefetch_related("videos", "images", "documents")
    )

    if q:
        topics_qs = topics_qs.filter(title__icontains=q)
        subtopics_qs = subtopics_qs.filter(title__icontains=q)

    items = []
    for t in topics_qs:
        program = t.subject.semester.program
        items.append({
            "kind": "topic",
            "id": t.id,
            "title": t.title,
            "program": program.short_name,
            "subject": t.subject.name,
            "has_video": bool(t.videos.all()),
            "has_image": bool(t.images.all()),
            "has_doc": bool(t.documents.all()),
            "sort_key": (program.short_name, t.subject.semester.number, t.subject.name, t.order, t.title),
        })
    for s in subtopics_qs:
        t = s.topic
        program = t.subject.semester.program
        items.append({
            "kind": "subtopic",
            "id": s.id,
            "title": s.title,
            "program": program.short_name,
            "subject": t.subject.name,
            "has_video": bool(s.videos.all()),
            "has_image": bool(s.images.all()),
            "has_doc": bool(s.documents.all()),
            "sort_key": (program.short_name, t.subject.semester.number, t.subject.name, t.order, s.order, s.title),
        })

    items.sort(key=lambda x: (x["sort_key"][0], x["sort_key"][1], x["sort_key"][2], str(x["sort_key"][3:])))
    return items


def topic_browse(request):
    q = request.GET.get("q", "").strip()
    items = _collect_browse_items(q)
    paginator = Paginator(items, TOPIC_BROWSE_PAGE_SIZE)
    page_obj = paginator.get_page(1)
    context = {
        "page_obj": page_obj,
        "query": q,
        "page_title": "Browse Topics",
    }
    return render(request, "academics/topic_browse.html", context)


def topic_browse_partial(request):
    q = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    items = _collect_browse_items(q)
    paginator = Paginator(items, TOPIC_BROWSE_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "query": q}
    return render(request, "partials/topic_grid_items.html", context)



# ---------------------------------------------------------------------------
# Books — searchable gallery of every Subject that has a full-book Drive link
# ---------------------------------------------------------------------------
def _collect_book_items(q):
    subjects_qs = (
        Subject.published.exclude(book_drive_link="")
        .select_related("semester", "semester__program")
    )
    if q:
        subjects_qs = subjects_qs.filter(name__icontains=q)

    items = []
    for s in subjects_qs:
        program = s.semester.program
        items.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "program": program.short_name,
            "semester": s.semester.display_name,
            "book_link": s.book_drive_link,
            "sort_key": (program.short_name, s.semester.number, s.name),
        })
    items.sort(key=lambda x: x["sort_key"])
    return items


def book_browse(request):
    q = request.GET.get("q", "").strip()
    items = _collect_book_items(q)
    paginator = Paginator(items, TOPIC_BROWSE_PAGE_SIZE)
    page_obj = paginator.get_page(1)
    context = {"page_obj": page_obj, "query": q, "page_title": "Books"}
    return render(request, "academics/book_browse.html", context)


def book_browse_partial(request):
    q = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    items = _collect_book_items(q)
    paginator = Paginator(items, TOPIC_BROWSE_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "query": q}
    return render(request, "partials/book_grid_items.html", context)