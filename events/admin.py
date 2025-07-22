from django.contrib import admin
from .models import Event, Location, UserProfile
from unfold.admin import ModelAdmin


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ["address", "city", "country"]
    search_fields = ["address", "city", "country"]
    list_filter = ["country", "city"]


@admin.register(Event)
class EventAdmin(ModelAdmin):
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


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ["user", "created_at", "updated_at"]
    search_fields = ["user__username", "bio"]
    list_filter = ["created_at"]
