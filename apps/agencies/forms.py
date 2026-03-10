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

    def _check_image_dimensions(self, field_name, min_w, min_h):
        img = self.cleaned_data.get(field_name)
        if img and hasattr(img, 'file'):
            try:
                from PIL import Image
                pil = Image.open(img)
                w, h = pil.size
                if w < min_w or h < min_h:
                    raise forms.ValidationError(
                        f"Image must be at least {min_w}×{min_h} px (uploaded: {w}×{h} px)."
                    )
            except Exception as exc:
                if isinstance(exc, forms.ValidationError):
                    raise
        return img

    def clean_logo(self):
        return self._check_image_dimensions("logo", 200, 200)

    def clean_cover_image(self):
        return self._check_image_dimensions("cover_image", 1200, 400)
