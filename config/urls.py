from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.academics.sitemaps import (
    ProgramSitemap,
    SubjectSitemap,
    TopicSitemap,
)
from apps.core.views import ads_txt, robots_txt

sitemaps = {
    "programs": ProgramSitemap,
    "subjects": SubjectSitemap,
    "topics": TopicSitemap,
}

urlpatterns = [
    path("admins-portal-site-4224/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.academics.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("ads.txt", ads_txt, name="ads_txt"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "iSchool LMS Administration"
admin.site.site_title = "iSchool LMS Admin"
admin.site.index_title = "Manage programs, subjects & past papers"

handler404 = "apps.core.views.custom_404"
handler500 = "apps.core.views.custom_500"
