from django.db.models import F

from .models import PageVisit


def log_visit(path, title=""):
    """
    Increments the visit counter for a given path (creates the row if it
    doesn't exist yet). Uses F() to avoid race conditions under load.
    """
    obj, created = PageVisit.objects.get_or_create(
        path=path, defaults={"title": title, "visit_count": 1}
    )
    if not created:
        update_fields = ["visit_count"]
        PageVisit.objects.filter(pk=obj.pk).update(visit_count=F("visit_count") + 1)
        if title and title != obj.title:
            PageVisit.objects.filter(pk=obj.pk).update(title=title)