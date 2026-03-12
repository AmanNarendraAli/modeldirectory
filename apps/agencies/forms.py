from django import forms
from django.forms import inlineformset_factory
from .models import Agency, AgencyRequirement, AgencyPortfolioPost, AgencyPortfolioAsset

INPUT_CLASS = "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"


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
            "is_roster_public",
            "is_requirements_public",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({"class": INPUT_CLASS})

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


class AgencyRequirementForm(forms.ModelForm):
    class Meta:
        model = AgencyRequirement
        fields = [
            "category",
            "min_height_cm",
            "max_height_cm",
            "age_min",
            "age_max",
            "min_bust_cm",
            "max_bust_cm",
            "min_waist_cm",
            "max_waist_cm",
            "min_hips_cm",
            "max_hips_cm",
            "min_inseam_cm",
            "max_inseam_cm",
            "preferred_hair_colors",
            "preferred_eye_colors",
            "accepts_beginners",
            "notes",
            "application_guidance_text",
            "is_current",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
            "application_guidance_text": forms.Textarea(attrs={"rows": 2}),
            "preferred_hair_colors": forms.TextInput(attrs={"placeholder": "e.g. Brown, Black, Dark"}),
            "preferred_eye_colors": forms.TextInput(attrs={"placeholder": "e.g. Brown, Green, Hazel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({"class": INPUT_CLASS})


class AgencyPortfolioPostForm(forms.ModelForm):
    class Meta:
        model = AgencyPortfolioPost
        fields = ["title", "caption", "cover_image", "is_public"]
        widgets = {
            "caption": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not (self.instance and self.instance.pk and self.instance.cover_image):
            self.fields["cover_image"].required = True
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": INPUT_CLASS})


AgencyPortfolioAssetFormset = inlineformset_factory(
    AgencyPortfolioPost,
    AgencyPortfolioAsset,
    fields=["image", "alt_text", "display_order"],
    extra=1,
    max_num=10,
    validate_max=True,
    can_delete=True,
)


AgencyRequirementFormSet = inlineformset_factory(
    Agency,
    AgencyRequirement,
    form=AgencyRequirementForm,
    extra=1,
    can_delete=True,
    max_num=10,
)
