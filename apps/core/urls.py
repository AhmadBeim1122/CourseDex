from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service/", views.terms, name="terms"),
    path("disclaimer/", views.disclaimer, name="disclaimer"),
    path("favicon.svg", views.favicon_svg, name="favicon_svg"),

    path("chat/widget/", views.chat_widget, name="chat_widget"),
    path("chat/send/", views.chat_send, name="chat_send"),
    path("staff/chat/", views.chat_admin_page, name="chat_admin_page"),
    path("staff/chat/list/", views.chat_admin_list_partial, name="chat_admin_list_partial"),
    path("staff/chat/<int:visitor_id>/thread/", views.chat_admin_thread, name="chat_admin_thread"),
    path("staff/chat/<int:visitor_id>/reply/", views.chat_admin_reply, name="chat_admin_reply"),
]
