from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User
from apps.models_app.models import ModelProfile


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)
    role = forms.ChoiceField(
        choices=[
            (User.Role.MODEL, "Model"),
            (User.Role.AGENCY_STAFF, "Agency Staff"),
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
            "custom_agency_name",
            "is_public",
            "is_discoverable",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "placeholder": "YYYY-MM-DD"}),
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

    def clean_represented_by_agency(self):
        agency = self.cleaned_data.get("represented_by_agency")
        if agency and self.instance and self.instance.pk:
            from apps.agencies.models import AgencyBan
            if AgencyBan.objects.filter(model_profile=self.instance, agency=agency).exists():
                raise forms.ValidationError(
                    f"You were removed by {agency.name}. Only they can add you back."
                )
        return agency
