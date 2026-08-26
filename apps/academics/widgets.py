from django import forms


class RichTextWidget(forms.Textarea):
    """
    A textarea enhanced with a Quill.js WYSIWYG editor in the Django admin.
    The real <textarea> stays in the DOM (hidden) so normal Django form
    submission still works — Quill just keeps it in sync.
    """

    class Media:
        css = {
            "all": ("https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css",)
        }
        js = (
            "https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js",
            "js/admin_richtext.js",
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        css_classes = (attrs.get("class", "") + " rich-text-source").strip()
        attrs["class"] = css_classes
        attrs["style"] = "display:none;"
        return attrs