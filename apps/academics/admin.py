from django.contrib import admin
from django.utils.html import format_html

from django.http import JsonResponse

from .ai_service import (
    PROVIDERS, generate_explanation, generate_solution, get_usage_summary,
    log_usage, ocr_extract_text_gemini, ocr_extract_text_tesseract,
)
from .models import (
    PastPaper, Program, Semester, Subject, SubTopic, SubTopicDocument,
    SubTopicImage, SubTopicVideo, Topic, TopicDocument, TopicImage, TopicVideo,
)
from .widgets import RichTextWidget

import re

from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse


TOPIC_BOUNDARY_RE = re.compile(r'(?:^|(?<=[.,]\s))([A-Z][A-Za-z0-9 /\-]{2,70}):\s*')


def split_body_to_subtopics(body):
    """Splits a topic's body text into individual subtopic items on commas/semicolons."""
    if not body:
        return []
    raw_parts = re.split(r'[;,]', body)
    subtopics = []
    for part in raw_parts:
        part = part.strip().strip(".").strip()
        if part:
            subtopics.append(part)
    return subtopics


def split_outline_to_topics(text):
    """
    Splits a pasted subject outline into topics with nested subtopics.
    Treats "Heading: details, more details..." patterns as topic
    boundaries; everything after a heading (comma/semicolon separated)
    becomes that topic's subtopics. Falls back to sentence splitting
    (as single-subtopic topics) if no headings are found.

    Returns a list of dicts: {"title": str, "content": str, "subtopics": [str, ...]}
    """
    text = " ".join(text.strip().split())
    if not text:
        return []

    matches = list(TOPIC_BOUNDARY_RE.finditer(text))
    if not matches:
        parts = re.split(r'(?<=\.)\s+', text)
        topics = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            title = " ".join(part.split()[:8]).rstrip(".,;")
            topics.append({"title": title, "content": part, "subtopics": []})
        return topics

    topics = []
    if matches[0].start() > 0:
        leading = text[: matches[0].start()].strip()
        if leading:
            title = " ".join(leading.split()[:8]).rstrip(".,;")
            topics.append({"title": title, "content": leading, "subtopics": []})

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        content = f"{title}: {body}" if body else title
        subtopics = split_body_to_subtopics(body)
        topics.append({"title": title, "content": content, "subtopics": subtopics})

    return topics


class OutlineImportForm(forms.Form):
    outline_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 12, "class": "vLargeTextField"}),
        label="Paste outline",
        help_text=(
            "Paste the full subject outline. Each heading followed by a "
            "colon becomes a separate topic — everything after it becomes "
            "that topic's notes/subtopics."
        ),
    )
    replace_existing = forms.BooleanField(
        required=False,
        initial=False,
        label="Delete existing topics for this subject first",
    )

# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------
class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 1
    fields = ("number", "name", "is_published")


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ("name", "code", "credit_hours", "order", "is_published")
    show_change_link = True

class SubTopicInlineForm(forms.ModelForm):
    class Meta:
        model = SubTopic
        fields = "__all__"
        widgets = {"content": RichTextWidget(attrs={"rows": 6})}


class SubTopicInline(admin.TabularInline):
    model = SubTopic
    form = SubTopicInlineForm
    extra = 1
    fields = ("order", "title", "content")
    show_change_link = True

class TopicVideoInline(admin.TabularInline):
    model = TopicVideo
    extra = 1
    fields = ("order", "youtube_url", "title")


class TopicDocumentInline(admin.TabularInline):
    model = TopicDocument
    extra = 1
    fields = ("order", "drive_link", "title")


class SubTopicVideoInline(admin.TabularInline):
    model = SubTopicVideo
    extra = 1
    fields = ("order", "youtube_url", "title")

class SubTopicImageInline(admin.TabularInline):
    model = SubTopicImage
    extra = 1
    max_num = 6
    fields = ("drive_link", "caption", "order")


class SubTopicDocumentInline(admin.TabularInline):
    model = SubTopicDocument
    extra = 1
    fields = ("order", "drive_link", "title")    

class TopicImageInline(admin.TabularInline):
    model = TopicImage
    extra = 1
    max_num = 6
    fields = ("drive_link", "caption", "order")


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ("order", "title", "is_published")
    show_change_link = True


class PastPaperInline(admin.TabularInline):
    model = PastPaper
    extra = 1
    fields = ("year", "exam_type", "paper_drive_link", "solution_type", "is_published")


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("short_name", "name", "total_semesters", "subject_count_display", "is_published", "order")
    list_editable = ("order", "is_published")
    search_fields = ("name", "short_name")
    prepopulated_fields = {"slug": ("short_name",)}
   
    fieldsets = (
        (None, {"fields": ("name", "short_name", "slug", "description")}),
        ("Structure", {"fields": ("total_semesters", "icon_drive_link", "order", "is_published")}),
    )

    @admin.display(description="Published subjects")
    def subject_count_display(self, obj):
        return obj.subject_count

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Convenience: auto-create any missing semesters up to total_semesters
        existing = set(obj.semesters.values_list("number", flat=True))
        for n in obj.semester_numbers:
            if n not in existing:
                Semester.objects.create(program=obj, number=n)


# ---------------------------------------------------------------------------
# Semester
# ---------------------------------------------------------------------------
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("__str__", "program", "number", "subject_count_display", "is_published")
    list_filter = ("program",)
    inlines = [SubjectInline]

    @admin.display(description="Subjects")
    def subject_count_display(self, obj):
        return obj.subject_count


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "semester", "topic_count_display", "past_paper_count_display", "is_published")
    list_filter = ("semester__program", "semester")
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TopicInline, PastPaperInline]
    change_form_template = "admin/academics/subject/change_form.html"

    @admin.display(description="Topics")
    def topic_count_display(self, obj):
        return obj.topic_count

    @admin.display(description="Past papers")
    def past_paper_count_display(self, obj):
        return obj.past_papers.count()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:subject_id>/import-outline/",
                self.admin_site.admin_view(self.import_outline_view),
                name="academics_subject_import_outline",
            ),
        ]
        return custom + urls

    def import_outline_view(self, request, subject_id):
        subject = get_object_or_404(Subject, pk=subject_id)
        if request.method == "POST":
            form = OutlineImportForm(request.POST)
            if form.is_valid():
                parsed = split_outline_to_topics(form.cleaned_data["outline_text"])
                if form.cleaned_data["replace_existing"]:
                    subject.topics.all().delete()
                start_order = subject.topics.count()
                created = 0
                subtopics_created = 0
                for i, item in enumerate(parsed, start=1):
                    topic = Topic.objects.create(
                        subject=subject,
                        title=(item["title"] or f"Topic {start_order + i}")[:200],
                        order=start_order + i,
                        content=item["content"],
                    )
                    created += 1
                    for j, sub_title in enumerate(item["subtopics"], start=1):
                        SubTopic.objects.create(topic=topic, title=sub_title[:255], order=j)
                        subtopics_created += 1
                self.message_user(
                    request,
                    f"Created {created} topic(s) and {subtopics_created} subtopic(s) from the pasted outline.",
                )
                return redirect(reverse("admin:academics_subject_change", args=[subject.pk]))
        else:
            form = OutlineImportForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
            subject=subject,
            title=f"Import topics for {subject.name}",
        )
        return render(request, "admin/academics/subject/import_outline.html", context)

# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------
class TopicAdminForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = "__all__"
        widgets = {"content": RichTextWidget()}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    form = TopicAdminForm
    list_display = ("title", "subject", "order", "subtopic_count_display", "has_video", "has_document", "image_count_display", "is_published")
    list_filter = ("subject__semester__program", "subject")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SubTopicInline, TopicVideoInline, TopicDocumentInline, TopicImageInline]

    class Media:
        js = ("js/admin_ai_buttons.js",)
        css = {"all": ("css/admin-overrides.css",)}

    @admin.display(description="Subtopics")
    def subtopic_count_display(self, obj):
        return obj.subtopics.count()

    def get_urls(self):
        custom = [
            path("ai/generate/", self.admin_site.admin_view(self.ai_generate_view), name="academics_ai_generate"),
            path("ai/usage/", self.admin_site.admin_view(self.ai_usage_view), name="academics_ai_usage"),
        ]
        return custom + super().get_urls()

    def ai_generate_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "POST required"}, status=405)
        provider = request.POST.get("provider")
        title = request.POST.get("title", "").strip()
        if not title:
            return JsonResponse({"ok": False, "error": "Title is empty."})
        if provider not in PROVIDERS:
            return JsonResponse({"ok": False, "error": "Unknown provider."})
        try:
            text = generate_explanation(provider, title)
            log_usage(provider)
            return JsonResponse({"ok": True, "text": text})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)})

    def ai_usage_view(self, request):
        return JsonResponse({"summary": get_usage_summary()})

    fieldsets = (
        (None, {"fields": ("subject", "title", "slug", "order", "is_published")}),
        ("Study content", {"fields": ("content",)}),
    )

    @admin.display(boolean=True, description="Video")
    def has_video(self, obj):
        return obj.videos.exists()

    @admin.display(boolean=True, description="Document")
    def has_document(self, obj):
        return obj.documents.exists()

    @admin.display(description="Images")
    def image_count_display(self, obj):
        return obj.images.count()
# ---------------------------------------------------------------------------
# Sub-Topic
# ---------------------------------------------------------------------------

class SubTopicAdminForm(forms.ModelForm):
    class Meta:
        model = SubTopic
        fields = "__all__"
        widgets = {"content": RichTextWidget()}


@admin.register(SubTopic)
class SubTopicAdmin(admin.ModelAdmin):
    form = SubTopicAdminForm
    list_display = ("title", "topic", "order", "video_count_display", "image_count_display", "document_count_display")
    list_filter = ("topic__subject__semester__program",)
    search_fields = ("title", "content")
    inlines = [SubTopicVideoInline, SubTopicImageInline, SubTopicDocumentInline]

    class Media:
        js = ("js/admin_ai_buttons.js",)
        css = {"all": ("css/admin-overrides.css",)}

    @admin.display(description="Videos")
    def video_count_display(self, obj):
        return obj.videos.count()

    @admin.display(description="Images")
    def image_count_display(self, obj):
        return obj.images.count()

    @admin.display(description="Documents")
    def document_count_display(self, obj):
        return obj.documents.count()

# ---------------------------------------------------------------------------
# Past Paper
# ---------------------------------------------------------------------------
class PastPaperAdminForm(forms.ModelForm):
    class Meta:
        model = PastPaper
        fields = "__all__"
        widgets = {"solution_text": RichTextWidget()}


@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    form = PastPaperAdminForm
    list_display = ("subject", "year", "exam_type", "solution_type", "paper_link", "is_published")
    list_filter = ("subject__semester__program", "year", "exam_type", "solution_type")
    search_fields = ("subject__name",)
    fieldsets = (
        (None, {"fields": ("subject", "year", "exam_type", "is_published")}),
        ("Question paper", {"fields": ("paper_drive_link", "extracted_text")}),
        (
            "Solution",
            {"fields": ("solution_type", "solution_text", "solution_drive_link")},
        ),
    )

    class Media:
        js = ("js/admin_pastpaper_ai.js",)
        css = {"all": ("css/admin-overrides.css",)}

    @admin.display(description="Paper")
    def paper_link(self, obj):
        if obj.paper_drive_link:
            return format_html('<a href="{}" target="_blank">Open ↗</a>', obj.paper_drive_link)
        return "-"

    def get_urls(self):
        custom = [
            path("ai/ocr/", self.admin_site.admin_view(self.ai_ocr_view), name="academics_pastpaper_ocr"),
            path("ai/solve/", self.admin_site.admin_view(self.ai_solve_view), name="academics_pastpaper_solve"),
        ]
        return custom + super().get_urls()

    def ai_ocr_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "POST required"}, status=405)
        drive_link = request.POST.get("drive_link", "").strip()
        method = request.POST.get("method", "gemini")
        if not drive_link:
            return JsonResponse({"ok": False, "error": "Paste the paper's Drive link first."})
        try:
            if method == "tesseract":
                text = ocr_extract_text_tesseract(drive_link)
            else:
                text = ocr_extract_text_gemini(drive_link)
            return JsonResponse({"ok": True, "text": text, "method": method})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)})

    def ai_solve_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "POST required"}, status=405)
        provider = request.POST.get("provider")
        paper_text = request.POST.get("paper_text", "").strip()
        if not paper_text:
            return JsonResponse({"ok": False, "error": "No extracted paper text to solve."})
        if provider not in PROVIDERS:
            return JsonResponse({"ok": False, "error": "Unknown provider."})
        try:
            text = generate_solution(provider, paper_text)
            log_usage(provider)
            return JsonResponse({"ok": True, "text": text})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)})




# ---------------------------------------------------------------------------
# Ai provider
# ---------------------------------------------------------------------------
from .models import AIProviderUsage


@admin.register(AIProviderUsage)
class AIProviderUsageAdmin(admin.ModelAdmin):
    list_display = ("provider", "date", "count")
    list_filter = ("provider", "date")
    ordering = ("-date",)
    readonly_fields = ("provider", "date", "count")

    def has_add_permission(self, request):
        return False