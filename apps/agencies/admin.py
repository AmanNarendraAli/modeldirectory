from django.contrib import admin
from .models import Agency, AgencyRequirement, AgencyHighlight, AgencyStaff, AgencyPortfolioPost, AgencyPortfolioAsset, AgencyRequest


class AgencyRequirementInline(admin.TabularInline):
    model = AgencyRequirement
    extra = 1


class AgencyHighlightInline(admin.TabularInline):
    model = AgencyHighlight
    extra = 1


class AgencyStaffInline(admin.TabularInline):
    model = AgencyStaff
    extra = 1


class AgencyPortfolioAssetInline(admin.TabularInline):
    model = AgencyPortfolioAsset
    extra = 1


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active", "is_accepting_applications", "is_featured", "verification_status")
    list_filter = ("is_active", "is_accepting_applications", "is_featured", "verification_status", "city")
    search_fields = ("name", "slug", "city", "contact_email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [AgencyRequirementInline, AgencyHighlightInline, AgencyStaffInline]


@admin.register(AgencyPortfolioPost)
class AgencyPortfolioPostAdmin(admin.ModelAdmin):
    list_display = ("agency", "title", "is_public", "created_at")
    list_filter = ("agency", "is_public")
    search_fields = ("agency__name", "title")
    inlines = [AgencyPortfolioAssetInline]


@admin.register(AgencyRequirement)
class AgencyRequirementAdmin(admin.ModelAdmin):
    list_display = ("agency", "category", "min_height_cm", "is_current", "accepts_beginners")
    list_filter = ("category", "is_current", "accepts_beginners")
    search_fields = ("agency__name",)


@admin.register(AgencyHighlight)
class AgencyHighlightAdmin(admin.ModelAdmin):
    list_display = ("agency", "title", "year", "display_order")
    list_filter = ("agency",)
    search_fields = ("agency__name", "title", "related_model_name", "related_brand_name")


@admin.register(AgencyStaff)
class AgencyStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "agency", "role_title", "can_review_applications", "is_primary_contact")
    list_filter = ("agency", "can_review_applications", "is_primary_contact")
    search_fields = ("user__email", "user__full_name", "agency__name")


@admin.register(AgencyRequest)
class AgencyRequestAdmin(admin.ModelAdmin):
    list_display = ("agency_name", "contact_name", "contact_email", "agency_city", "role_at_agency", "status", "created_agency_link", "created_at")
    list_filter = ("status",)
    search_fields = ("agency_name", "contact_name", "contact_email", "agency_city")
    readonly_fields = ("created_agency",)

    @admin.display(description="Agency")
    def created_agency_link(self, obj):
        if obj.created_agency:
            from django.utils.html import format_html
            return format_html('<a href="/admin/agencies/agency/{}/change/">{}</a>', obj.created_agency.pk, obj.created_agency.name)
        return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == AgencyRequest.Status.ACCEPTED and not obj.created_agency:
            agency = Agency.objects.create(
                name=obj.agency_name,
                city=obj.agency_city or "",
                website_url=obj.agency_website or "",
                instagram_url=obj.agency_instagram or "",
                description=obj.about_agency or "",
                contact_email=obj.contact_email,
                is_active=True,
                is_accepting_applications=False,
                created_by_admin=request.user,
            )
            obj.created_agency = agency
            obj.save(update_fields=["created_agency"])
            from django.contrib import messages
            messages.success(request, f'Agency "{agency.name}" created. Edit it to add logo, requirements, etc.')
