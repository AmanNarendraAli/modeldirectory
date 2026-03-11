from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_note"]
        widgets = {
            "cover_note": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "Introduce yourself and explain why you'd be a great fit for this agency…",
                "class": "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400",
            }),
        }
        labels = {
            "cover_note": "Cover Note",
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["feedback"]
        widgets = {
            "feedback": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Add feedback for this applicant (visible to them in their dashboard)…",
                "class": "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400",
            }),
        }
        labels = {
            "feedback": "Feedback",
        }
