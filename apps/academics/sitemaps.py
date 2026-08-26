from django.contrib.sitemaps import Sitemap

from .models import Program, Subject, Topic


class ProgramSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Program.published.all()

    def location(self, obj):
        return obj.get_absolute_url()


class SubjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Subject.published.filter(semester__is_published=True)

    def location(self, obj):
        return obj.get_absolute_url()


class TopicSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Topic.published.filter(
            subject__is_published=True, subject__semester__is_published=True
        )

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at
