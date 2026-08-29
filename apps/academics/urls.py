from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    # Courses / study material
    path("courses/", views.program_list, name="program_list"),
    path("courses/<slug:program_slug>/", views.semester_list, name="semester_list"),
    path(
        "courses/<slug:program_slug>/<int:semester_number>/",
        views.subject_list,
        name="subject_list",
    ),
    path(
        "courses/<slug:program_slug>/<int:semester_number>/<slug:subject_slug>/",
        views.topic_list,
        name="topic_list",
    ),
    path(
        "courses/<slug:program_slug>/<int:semester_number>/<slug:subject_slug>/<slug:topic_slug>/",
        views.topic_detail,
        name="topic_detail",
    ),
    path(
        "courses/<slug:program_slug>/<int:semester_number>/<slug:subject_slug>/<slug:topic_slug>/<slug:subtopic_slug>/",
        views.subtopic_detail,
        name="subtopic_detail",
    ),
    # Past papers
    path("past-papers/", views.pastpaper_program_list, name="pastpaper_program_list"),
    path(
        "past-papers/<slug:program_slug>/",
        views.pastpaper_semester_list,
        name="pastpaper_semester_list",
    ),
    path(
        "past-papers/<slug:program_slug>/<int:semester_number>/",
        views.pastpaper_subject_list,
        name="pastpaper_subject_list",
    ),
    path(
        "past-papers/<slug:program_slug>/<int:semester_number>/<slug:subject_slug>/",
        views.pastpaper_year_list,
        name="pastpaper_year_list",
    ),
    path(
        "past-papers/<slug:program_slug>/<int:semester_number>/<slug:subject_slug>/<int:year>/",
        views.pastpaper_detail,
        name="pastpaper_detail",
    ),
    path(
        "api/content/<str:kind>/<int:pk>/",
        views.keyword_content_api,
        name="keyword_content_api",
    ),
    path("topics/", views.topic_browse, name="topic_browse"),
    path("topics/partial/", views.topic_browse_partial, name="topic_browse_partial"),
    path("books/", views.book_browse, name="book_browse"),
    path("books/partial/", views.book_browse_partial, name="book_browse_partial"),

    path("staff-ai/topic/generate/", views.ai_topic_generate, name="ai_topic_generate"),
    path("staff-ai/topic/usage/", views.ai_topic_usage, name="ai_topic_usage"),
    path("staff-ai/pastpaper/ocr/", views.ai_pastpaper_ocr, name="ai_pastpaper_ocr"),
    path("staff-ai/pastpaper/solve/", views.ai_pastpaper_solve, name="ai_pastpaper_solve"),
]
