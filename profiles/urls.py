"""
URL configuration for the profiles application.

Defines URL patterns for viewing and managing user profiles.
"""

from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path("", views.user_profile, name="my_profile"),
    path("users/", views.users_list, name="users_list"),  # Move this before the username pattern
    path("edit/", views.edit_profile, name="edit_profile"),
    path("api/update/", views.update_profile, name="update_profile"),
    path("api/favorites/<int:favorite_id>/remove/", views.remove_favorite, name="remove_favorite"),
    path("api/rsvp/update/", views.update_rsvp, name="update_rsvp"),
    path("api/delete/", views.delete_profile, name="delete_profile"),
    path('<str:username>/', views.user_profile, name='user_profile'),  # Keep this last
]