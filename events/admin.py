from django.contrib import admin
from .models import Event, Location
# from unfold.admin import ModelAdmin  # Temporarily disabled


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

# from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm  # Temporarily disabled


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Temporarily using standard Django admin
    # Forms loaded from `unfold.forms`
    # form = UserChangeForm
    # add_form = UserCreationForm
    # change_password_form = AdminPasswordChangeForm
    pass


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["address", "city", "country"]
    search_fields = ["address", "city", "country"]
    list_filter = ["country", "city"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "start_date",
        "end_date",
        "event_type",
        "skill_level",
        "published",
    ]
    list_filter = ["published", "event_type", "skill_level", "start_date"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "start_date"
    ordering = ["-start_date"]
