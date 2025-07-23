"""
URL configuration for the profiles application.

Defines URL patterns for viewing and managing user profiles, including
enhanced signup and onboarding flows.
"""

from django.urls import path
from . import views, signup_views

app_name = 'profiles'

urlpatterns = [
    path("", views.user_profile, name="my_profile"),
    path("users/", views.users_list, name="users_list"),  # Move this before the username pattern
    # path("edit/", views.edit_profile, name="edit_profile"),  # Deprecated - using inline editing
    
    # Enhanced signup and onboarding
    path("complete-signup/", signup_views.complete_signup, name="complete_signup"),
    path("onboarding/", signup_views.onboarding_tour, name="onboarding_tour"),
    path("signup-success/", signup_views.signup_success, name="signup_success"),
    path("api/signup-validation/", signup_views.signup_step_validation, name="signup_validation"),
    
    # Social features - Following system
    path("api/follow/<int:user_id>/", views.follow_user, name="follow_user"),
    path("api/unfollow/<int:user_id>/", views.unfollow_user, name="unfollow_user"),
    path("followers/<int:user_id>/", views.followers_list, name="followers_list"),
    path("following/<int:user_id>/", views.following_list, name="following_list"),
    path("activity-feed/", views.activity_feed, name="activity_feed"),
    
    # Enhanced API endpoints
    path("api/update/", views.update_profile_api, name="update_profile_api"),
    path("api/avatar/", views.upload_avatar_api, name="upload_avatar_api"),
    path("api/completion/<int:user_id>/", views.get_completion_api, name="get_completion_api"),
    path("api/test-csrf/", views.test_csrf_api, name="test_csrf_api"),
    
    # Legacy API endpoints
    path("api/completion-suggestions/", views.profile_completion_suggestions, name="completion_suggestions"),
    path("api/favorites/<int:favorite_id>/remove/", views.remove_favorite, name="remove_favorite"),
    path("api/rsvp/update/", views.update_rsvp, name="update_rsvp"),
    path("api/delete/", views.delete_profile, name="delete_profile"),
    
    path('<str:username>/', views.user_profile, name='user_profile'),  # Keep this last
]