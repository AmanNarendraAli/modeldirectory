from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User
from apps.models_app.models import ModelProfile


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)
    role = forms.ChoiceField(
        choices=[
            (User.Role.MODEL, "I'm a Model"),
            (User.Role.AGENCY_STAFF, "I'm Agency Staff"),
        ],
        widget=forms.RadioSelect,
        initial=User.Role.MODEL,
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "role", "password1", "password2")


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = ModelProfile
        fields = [
            "public_display_name",
            "city",
            "date_of_birth",
            "gender",
            "bio",
            "height_cm",
            "bust_cm",
            "waist_cm",
            "hips_cm",
            "inseam_cm",
            "shoe_size",
            "hair_color",
            "eye_color",
            "profile_image",
            "cover_image",
            "instagram_url",
            "website_url",
            "contact_email",
            "phone_number",
            "available_for_editorial",
            "available_for_runway",
            "available_for_commercial",
            "available_for_fittings",
            "represented_by_agency",
            "is_public",
            "is_discoverable",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
            "gender": forms.Select(),
            "represented_by_agency": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({
                    "class": "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
                })
        self.fields["represented_by_agency"].required = False
        self.fields["represented_by_agency"].empty_label = "— Independent (no agency) —"

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

    def clean_profile_image(self):
        return self._check_image_dimensions("profile_image", 400, 400)

    def clean_cover_image(self):
        return self._check_image_dimensions("cover_image", 1200, 400)
