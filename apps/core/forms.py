from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "class": "input"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "input"}),
            "subject": forms.TextInput(attrs={"placeholder": "Subject (optional)", "class": "input"}),
            "message": forms.Textarea(
                attrs={"placeholder": "How can we help?", "class": "input", "rows": 5}
            ),
        }
