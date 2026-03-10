from django import forms
from .models import Agency


class AgencyEditForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = [
            "name",
            "short_tagline",
            "description",
            "city",
            "headquarters_address",
            "website_url",
            "instagram_url",
            "contact_email",
            "logo",
            "cover_image",
            "is_accepting_applications",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({
                    "class": "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
                })
