from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("profile/<str:username>/", views.user_profile, name="user_profile"),
    path("profile/", views.user_profile, name="my_profile"),
    path("<slug:slug>/", views.event_details, name="event_details"),
    path("favorite/<slug:slug>/", views.toggle_favorite, name="toggle_favorite"),
    path("rsvp/<slug:slug>/", views.toggle_rsvp, name="toggle_rsvp"),
]
