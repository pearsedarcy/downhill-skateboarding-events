from django.contrib import admin
from .models import Event, Location, UserProfile


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "updated_at"]
    search_fields = ["user__username", "bio"]
    list_filter = ["created_at"]
