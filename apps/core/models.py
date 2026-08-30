from django.core.exceptions import ValidationError
from django.db import models


class SiteSetting(models.Model):
    """
    A singleton row the admin can edit from the Django admin to control
    site-wide text (About page, contact details, social links) without
    touching code. Only one row is ever allowed to exist.
    """

    site_tagline = models.CharField(
        max_length=200,
        default="Free notes, subject outlines & solved past papers for university students.",
    )
    about_text = models.TextField(
        blank=True,
        help_text="Shown on the About page. Write a few paragraphs about the site.",
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site settings"

    def clean(self):
        if not self.pk and SiteSetting.objects.exists():
            raise ValidationError("Only one Site Settings record is allowed. Edit the existing one.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    """Messages submitted through the public Contact page (HTMX form, no login)."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject or 'No subject'}"


class ChatVisitor(models.Model):
    """
    A single anonymous visitor's chat thread. Identified via the Django
    session (no login/signup) — the visitor's id is stored in
    request.session['chat_visitor_id'] after their first message.
    """
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Visitor"
        verbose_name_plural = "Chat Visitors"

    def __str__(self):
        return self.name

    @property
    def last_message(self):
        return self.messages.order_by("-created_at").first()

    @property
    def last_message_time(self):
        m = self.last_message
        return m.created_at if m else None

    @property
    def unread_count(self):
        return self.messages.filter(sender="user", is_read=False).count()


class ChatMessage(models.Model):
    class Sender(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    visitor = models.ForeignKey(ChatVisitor, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=Sender.choices)
    message = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False, help_text="Whether the admin has seen this (user) message.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.sender}: {self.message[:40]}"


class PageVisit(models.Model):
    """
    A basic per-URL visit counter — no per-user tracking, just a running
    count of how many times each page was loaded.
    """
    path = models.CharField(max_length=500, unique=True)
    title = models.CharField(max_length=255, blank=True)
    visit_count = models.PositiveIntegerField(default=0)
    last_visited = models.DateTimeField(auto_now=True)
    first_visited = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_count"]
        verbose_name = "Page Visit"
        verbose_name_plural = "Page Visits"

    def __str__(self):
        return f"{self.title or self.path} — {self.visit_count} visits"    