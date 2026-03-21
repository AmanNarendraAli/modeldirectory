from django import forms
from django.forms import inlineformset_factory
from .models import PortfolioPost, PortfolioAsset


class PortfolioPostForm(forms.ModelForm):
    class Meta:
        model = PortfolioPost
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
                field.widget.attrs.update({
                    "class": "w-full border border-stone-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
                })


class PortfolioAssetForm(forms.ModelForm):
    class Meta:
        model = PortfolioAsset
        fields = ["image", "alt_text", "display_order"]

    def has_changed(self):
        # For new (unsaved) forms, display_order is set by JS on all visible
        # slots.  If that's the only "change", the form is effectively empty.
        if not self.instance.pk and self.changed_data == ["display_order"]:
            return False
        return super().has_changed()


PortfolioAssetFormset = inlineformset_factory(
    PortfolioPost,
    PortfolioAsset,
    form=PortfolioAssetForm,
    extra=0,
    max_num=10,
    validate_max=True,
    can_delete=True,
)
