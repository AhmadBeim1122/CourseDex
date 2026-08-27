from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublishedManager(models.Manager):
    """Returns only rows flagged as published/active — used by the frontend."""

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


# ---------------------------------------------------------------------------
# Program  (e.g. BSIT, BSCS, BBA ...)
# ---------------------------------------------------------------------------
class Program(TimeStampedModel):
    name = models.CharField(
        max_length=150,
        help_text="Full program name, e.g. 'BS Information Technology'.",
    )
    short_name = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code shown throughout the site, e.g. 'BSIT'.",
    )
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(
        blank=True,
        help_text="A short paragraph about this program (helps SEO too).",
    )
    total_semesters = models.PositiveSmallIntegerField(
        default=8,
        help_text="How many semesters this program has (usually 8 for a 4-year degree).",
    )
    
    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers are shown first."
    )
    icon_drive_link = models.URLField(
        blank=True,
        help_text="Shareable Google Drive (or other) link to a square icon/logo image for this program (optional).",
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this program from the public site.",
    )

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self):
        return self.short_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.short_name or self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("academics:semester_list", kwargs={"program_slug": self.slug})

    def get_past_papers_url(self):
        return reverse(
            "academics:pastpaper_semester_list", kwargs={"program_slug": self.slug}
        )

    @property
    def semester_numbers(self):
        """List of semester numbers this program should have (for auto-creation)."""
        return list(range(1, self.total_semesters + 1))

    @property
    def subject_count(self):
        return Subject.published.filter(semester__program=self).count()


# ---------------------------------------------------------------------------
# Semester
# ---------------------------------------------------------------------------
class Semester(TimeStampedModel):
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="semesters"
    )
    number = models.PositiveSmallIntegerField(help_text="1, 2, 3 ...")
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional custom label. Defaults to 'Semester <number>'.",
    )
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["program", "number"]
        unique_together = ("program", "number")
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def __str__(self):
        return f"{self.program.short_name} - {self.display_name}"

    @property
    def display_name(self):
        return self.name or f"Semester {self.number}"

    def get_absolute_url(self):
        return reverse(
            "academics:subject_list",
            kwargs={"program_slug": self.program.slug, "semester_number": self.number},
        )

    def get_past_papers_url(self):
        return reverse(
            "academics:pastpaper_subject_list",
            kwargs={"program_slug": self.program.slug, "semester_number": self.number},
        )

    @property
    def subject_count(self):
        return self.subjects.filter(is_published=True).count()


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------
class Subject(TimeStampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="subjects"
    )
    name = models.CharField(max_length=150)
    code = models.CharField(
        max_length=30, blank=True, help_text="Optional subject code, e.g. CS-301."
    )
    slug = models.SlugField(max_length=170, blank=True)
    credit_hours = models.CharField(max_length=20, blank=True, help_text="e.g. '3(3-0)'")
    description = models.TextField(
        blank=True, help_text="Short overview of what this subject covers."
    )
    cover_image_drive_link = models.URLField(
        blank=True,
        help_text="Shareable Google Drive (or other) link to a cover image for this subject (optional — shown on the subject's page).",
    )
    book_drive_link = models.URLField(
        blank=True,
        help_text="Shareable Google Drive link to the full book/PDF/Doc for this subject (optional).",
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["order", "name"]
        unique_together = ("semester", "slug")
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.name} ({self.semester})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "academics:topic_list",
            kwargs={
                "program_slug": self.semester.program.slug,
                "semester_number": self.semester.number,
                "subject_slug": self.slug,
            },
        )

    def get_past_papers_url(self):
        return reverse(
            "academics:pastpaper_year_list",
            kwargs={
                "program_slug": self.semester.program.slug,
                "semester_number": self.semester.number,
                "subject_slug": self.slug,
            },
        )

    @property
    def topic_count(self):
        return self.topics.filter(is_published=True).count()

    @property
    def past_paper_years(self):
        return (
            self.past_papers.filter(is_published=True)
            .order_by("-year")
            .values_list("year", flat=True)
            .distinct()
        )


# ---------------------------------------------------------------------------
# Topic  (an item inside a subject's outline — 20-30 per subject typically)
# ---------------------------------------------------------------------------
def extract_youtube_id(url):
    """Extract the video id from common YouTube URL formats for embedding/thumbnails."""
    if not url:
        return ""
    url = url.strip()
    for marker in ("youtu.be/", "watch?v=", "embed/", "shorts/"):
        if marker in url:
            video_id = url.split(marker, 1)[1]
            return video_id.split("&")[0].split("?")[0].split("/")[0]
    return ""


class Topic(TimeStampedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    order = models.PositiveIntegerField(
        default=0, help_text="Position of this topic in the subject outline."
    )
    content = models.TextField(
        blank=True, help_text="Main study notes / explanation for this topic."
    )
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("subject", "slug")
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        s = self.subject
        return reverse(
            "academics:topic_detail",
            kwargs={
                "program_slug": s.semester.program.slug,
                "semester_number": s.semester.number,
                "subject_slug": s.slug,
                "topic_slug": self.slug,
            },
        )


class TopicVideo(TimeStampedModel):
    """A topic can have one or more YouTube videos attached."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="videos")
    youtube_url = models.URLField(help_text="A YouTube video link that explains this topic.")
    title = models.CharField(max_length=200, blank=True, help_text="Optional label shown above the video.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Topic video"
        verbose_name_plural = "Topic videos"

    def __str__(self):
        return self.title or self.youtube_url

    @property
    def embed_id(self):
        return extract_youtube_id(self.youtube_url)


class TopicDocument(TimeStampedModel):
    """A topic can have one or more shared documents (PDFs, slides, etc.) on Drive."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="documents")
    drive_link = models.URLField(help_text="Shareable Google Drive (or other) link to this document/PDF.")
    title = models.CharField(max_length=200, blank=True, help_text="e.g. 'Lecture slides', 'Handout PDF'.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Topic document"
        verbose_name_plural = "Topic documents"

    def __str__(self):
        return self.title or self.drive_link


class SubTopic(TimeStampedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    content = models.TextField(blank=True, help_text="Text explanation for this subtopic.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("topic", "slug")
        verbose_name = "Subtopic"
        verbose_name_plural = "Subtopics"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:280]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        t = self.topic
        s = t.subject
        return reverse(
            "academics:subtopic_detail",
            kwargs={
                "program_slug": s.semester.program.slug,
                "semester_number": s.semester.number,
                "subject_slug": s.slug,
                "topic_slug": t.slug,
                "subtopic_slug": self.slug,
            },
        )


class SubTopicVideo(TimeStampedModel):
    """A subtopic can also have one or more YouTube videos of its own."""
    subtopic = models.ForeignKey(SubTopic, on_delete=models.CASCADE, related_name="videos")
    youtube_url = models.URLField(help_text="A YouTube video link that explains this subtopic.")
    title = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Subtopic video"
        verbose_name_plural = "Subtopic videos"

    def __str__(self):
        return self.title or self.youtube_url

    @property
    def embed_id(self):
        return extract_youtube_id(self.youtube_url)

class SubTopicImage(TimeStampedModel):
    """2–6 images per subtopic; a Drive link (or uploaded file if you switch back)."""
    subtopic = models.ForeignKey(SubTopic, on_delete=models.CASCADE, related_name="images")
    drive_link = models.URLField(help_text="Shareable Google Drive (or other) link to this image.")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Subtopic image"
        verbose_name_plural = "Subtopic images"

    def __str__(self):
        return self.caption or f"Image for {self.subtopic.title}"

    @property
    def url(self):
        return self.drive_link


class SubTopicDocument(TimeStampedModel):
    """A subtopic can have one or more shared documents (PDFs, slides, etc.) on Drive."""
    subtopic = models.ForeignKey(SubTopic, on_delete=models.CASCADE, related_name="documents")
    drive_link = models.URLField(help_text="Shareable Google Drive (or other) link to this document/PDF.")
    title = models.CharField(max_length=200, blank=True, help_text="e.g. 'Lecture slides', 'Handout PDF'.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Subtopic document"
        verbose_name_plural = "Subtopic documents"

    def __str__(self):
        return self.title or self.drive_link




# ---------------------------------------------------------------------------
# API provider
# ---------------------------------------------------------------------------



class AIProviderUsage(TimeStampedModel):
    """Tracks how many AI-generation requests were made per provider per day,
    so the admin can see an estimated remaining daily quota."""
    provider = models.CharField(max_length=20)
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("provider", "date")
        verbose_name = "AI Provider Usage"
        verbose_name_plural = "AI Provider Usage"

    def __str__(self):
        return f"{self.provider} — {self.date} ({self.count})"    
# ---------------------------------------------------------------------------
# TopicImage  (2–6 images per topic; either uploaded or a Drive link)
# ---------------------------------------------------------------------------
class TopicImage(TimeStampedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="images")
    drive_link = models.URLField(
        help_text="Shareable Google Drive (or other) link to this image.",
    )
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Topic image"
        verbose_name_plural = "Topic images"

    def __str__(self):
        return self.caption or f"Image for {self.topic.title}"

    @property
    def url(self):
        return self.drive_link


# ---------------------------------------------------------------------------
# PastPaper
# ---------------------------------------------------------------------------
class PastPaper(TimeStampedModel):
    class ExamType(models.TextChoices):
        MID = "mid", "Mid Term"
        FINAL = "final", "Final Term"
        QUIZ = "quiz", "Quiz"
        ASSIGNMENT = "assignment", "Assignment"

    class SolutionType(models.TextChoices):
        NONE = "none", "No solution yet"
        TEXT = "text", "Written solution (text)"
        IMAGE = "image", "Solution image(s) / Drive link"

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="past_papers"
    )
    year = models.PositiveIntegerField(help_text="e.g. 2023")
    exam_type = models.CharField(
        max_length=20, choices=ExamType.choices, default=ExamType.FINAL
    )
    paper_drive_link = models.URLField(
        help_text="Shareable Google Drive link to the scanned/photographed question paper."
    )
    extracted_text = models.TextField(
        blank=True,
        help_text="Text extracted from the question paper image/PDF via OCR (not shown on the frontend yet).",
    )
    solution_type = models.CharField(
        max_length=10, choices=SolutionType.choices, default=SolutionType.NONE
    )
    solution_text = models.TextField(
        blank=True,
        help_text="Used when solution type is 'Written solution (text)'. "
        "You can generate this from the question paper using the OCR + AI "
        "tools above (near the Drive link field).",
    )
    solution_drive_link = models.URLField(
        blank=True,
        help_text="Used when the solution is one or more images/photos kept on Drive.",
    )
    is_published = models.BooleanField(default=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-year", "exam_type"]
        unique_together = ("subject", "year", "exam_type")
        verbose_name = "Past Paper"
        verbose_name_plural = "Past Papers"

    def __str__(self):
        return f"{self.subject.name} - {self.year} ({self.get_exam_type_display()})"

    def get_absolute_url(self):
        s = self.subject
        return reverse(
            "academics:pastpaper_detail",
            kwargs={
                "program_slug": s.semester.program.slug,
                "semester_number": s.semester.number,
                "subject_slug": s.slug,
                "year": self.year,
            },
        )

    @property
    def has_solution(self):
        return self.solution_type != self.SolutionType.NONE
