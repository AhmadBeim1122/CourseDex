from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from apps.academics.models import PastPaper, Program, Subject, Topic

from .forms import ContactForm
from .models import ChatMessage, ChatVisitor


def home(request):
    from .analytics import log_visit
    log_visit(request.path, "Home")
    programs = Program.published.all()[:8]
    stats = {
        "programs": Program.published.count(),
        "subjects": Subject.published.count(),
        "topics": Topic.published.count(),
        "past_papers": PastPaper.published.count(),
    }
    context = {
        "programs": programs,
        "stats": stats,
        "page_title": "Home",
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html", {"page_title": "About Us"})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            if request.htmx:
                html = render_to_string(
                    "partials/contact_success.html", {}, request=request
                )
                return HttpResponse(html)
            messages.success(request, "Thanks! Your message has been sent.")
            return redirect("core:contact")
        elif request.htmx:
            html = render_to_string(
                "partials/contact_form.html", {"form": form}, request=request
            )
            return HttpResponse(html)
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form, "page_title": "Contact Us"})


def privacy_policy(request):
    return render(request, "core/privacy.html", {"page_title": "Privacy Policy"})


def terms(request):
    return render(request, "core/terms.html", {"page_title": "Terms of Service"})


def disclaimer(request):
    return render(request, "core/disclaimer.html", {"page_title": "Disclaimer"})


def robots_txt(request):
    scheme = "https" if request.is_secure() else "http"
    site_url = f"{scheme}://{request.get_host()}"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def ads_txt(request):
    """
    Google AdSense verification file. Fill ADSENSE_PUBLISHER_ID in .env once
    you have an AdSense account, e.g. ADSENSE_PUBLISHER_ID=pub-1234567890123456
    """
    publisher_id = getattr(settings, "ADSENSE_CLIENT_ID", "")
    if not publisher_id:
        return HttpResponse(
            "# Add ADSENSE_CLIENT_ID to your .env once approved for AdSense",
            content_type="text/plain",
        )
    content = f"google.com, {publisher_id}, DIRECT, f08c47fec0942fa0"
    return HttpResponse(content, content_type="text/plain")


def custom_404(request, exception):
    return render(request, "core/404.html", status=404)


def custom_500(request):
    return render(request, "core/500.html", status=500)



def favicon_svg(request):
    """Generates the favicon on the fly using SITE_INITIALS from .env,
    so the icon always matches whatever site name/brand is configured."""
    initials = (getattr(settings, "SITE_INITIALS", "iS") or "iS")[:2]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="6" fill="#17203A"/>'
        f'<text x="16" y="21" font-family="Georgia,serif" font-size="14" '
        f'font-weight="700" fill="#E3A008" text-anchor="middle">{initials}</text>'
        '</svg>'
    )
    return HttpResponse(svg, content_type="image/svg+xml")







# ---------------------------------------------------------------------------
# Public chat widget (no login/signup — session-based visitor identity)
# ---------------------------------------------------------------------------
def chat_widget(request):
    visitor_id = request.session.get("chat_visitor_id")
    visitor = ChatVisitor.objects.filter(id=visitor_id).first() if visitor_id else None
    chat_messages = visitor.messages.order_by("created_at") if visitor else []
    return render(request, "partials/chat_panel.html", {"visitor": visitor, "messages": chat_messages})


@require_POST
def chat_send(request):
    message = request.POST.get("message", "").strip()

    visitor_id = request.session.get("chat_visitor_id")
    visitor = ChatVisitor.objects.filter(id=visitor_id).first() if visitor_id else None

    if not visitor:
        name = request.POST.get("name", "").strip()
        if not name or not message:
            return render(request, "partials/chat_panel.html", {
                "visitor": None,
                "messages": [],
                "errors": "Please enter both your name and a message.",
            })
        visitor = ChatVisitor.objects.create(name=name)
        request.session["chat_visitor_id"] = visitor.id
    elif not message:
        chat_messages = visitor.messages.order_by("created_at")
        return render(request, "partials/chat_panel.html", {
            "visitor": visitor,
            "messages": chat_messages,
            "errors": "Please enter a message.",
        })

    ChatMessage.objects.create(visitor=visitor, sender=ChatMessage.Sender.USER, message=message)
    chat_messages = visitor.messages.order_by("created_at")
    return render(request, "partials/chat_panel.html", {"visitor": visitor, "messages": chat_messages})



# ---------------------------------------------------------------------------
# Staff-only chat inbox (admin <-> visitor). No polling — updates only
# happen when the admin clicks a conversation, replies, or hits Refresh.
# ---------------------------------------------------------------------------
def _sorted_visitors():
    visitors = list(ChatVisitor.objects.all())
    visitors.sort(key=lambda v: v.last_message_time or v.created_at, reverse=True)
    return visitors


@staff_member_required
def chat_admin_page(request):
    context = {"visitors": _sorted_visitors(), "active_id": None, "page_title": "Chat Inbox"}
    return render(request, "core/chat_admin.html", context)


@staff_member_required
def chat_admin_list_partial(request):
    return render(request, "partials/chat_admin_list_items.html", {"visitors": _sorted_visitors(), "active_id": None})


@staff_member_required
def chat_admin_thread(request, visitor_id):
    visitor = get_object_or_404(ChatVisitor, id=visitor_id)
    ChatMessage.objects.filter(visitor=visitor, sender=ChatMessage.Sender.USER, is_read=False).update(is_read=True)
    chat_messages = visitor.messages.order_by("created_at")
    return render(request, "partials/chat_admin_thread_panel.html", {
        "visitor": visitor, "messages": chat_messages, "active_id": visitor.id,
    })


@staff_member_required
@require_POST
def chat_admin_reply(request, visitor_id):
    visitor = get_object_or_404(ChatVisitor, id=visitor_id)
    message = request.POST.get("message", "").strip()
    if message:
        ChatMessage.objects.create(visitor=visitor, sender=ChatMessage.Sender.ADMIN, message=message, is_read=True)
    chat_messages = visitor.messages.order_by("created_at")
    return render(request, "partials/chat_admin_thread_panel.html", {
        "visitor": visitor, "messages": chat_messages, "active_id": visitor.id,
    })