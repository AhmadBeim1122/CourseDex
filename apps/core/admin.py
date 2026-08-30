from django.contrib import admin

from .models import ChatMessage, ChatVisitor, ContactMessage, PageVisit, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("General", {"fields": ("site_tagline", "about_text")}),
        ("Contact details", {"fields": ("contact_email", "contact_phone")}),
        ("Social links", {"fields": ("facebook_url", "youtube_url", "whatsapp_url")}),
    )

    def has_add_permission(self, request):
        # Singleton: only allow adding if no row exists yet.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    list_editable = ("is_read",)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("sender", "message", "is_read", "created_at")
    can_delete = False


@admin.register(ChatVisitor)
class ChatVisitorAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "unread_count")
    readonly_fields = ("name", "created_at")
    inlines = [ChatMessageInline]

    def has_add_permission(self, request):
        return False



@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ("title", "path", "visit_count", "last_visited", "first_visited")
    search_fields = ("path", "title")
    ordering = ("-visit_count",)
    readonly_fields = ("path", "title", "visit_count", "last_visited", "first_visited")

    def has_add_permission(self, request):
        return False    