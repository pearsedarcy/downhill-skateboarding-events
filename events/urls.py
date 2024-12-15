from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("submit/", views.event_submission, name="submit"),
    path("edit/<slug:slug>/", views.event_submission, name="edit_event"),  # Changed name to match template references
    path("favorite/<slug:slug>/", views.toggle_favorite, name="toggle_favorite"),
    path("rsvp/<slug:slug>/", views.toggle_rsvp, name="toggle_rsvp"),
    path("<slug:slug>/", views.event_details, name="event_details"),
]
