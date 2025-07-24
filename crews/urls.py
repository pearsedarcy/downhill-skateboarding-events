"""
URL patterns for the crews app.

Defines URL routing for crew-related views including:
- Crew listing and detail pages
- Crew creation and management
- Membership management
- Invitation system
"""

from django.urls import path
from . import views

app_name = 'crews'

urlpatterns = [
    # Crew listing and discovery
    path('', views.crew_list, name='list'),
    path('create/', views.create_crew, name='create'),
    
    # Global invitation system (must come before crew-specific URLs)
    path('invitations/', views.my_invitations, name='my_invitations'),
    path('invitations/<int:invitation_id>/accept/', views.accept_invitation, name='accept_invitation'),
    path('invitations/<int:invitation_id>/decline/', views.decline_invitation, name='decline_invitation'),
    
    # Crew detail and management (slug patterns must come after more specific paths)
    path('<slug:slug>/', views.crew_detail, name='detail'),
    path('<slug:slug>/edit/', views.edit_crew, name='edit'),
    path('<slug:slug>/delete/', views.delete_crew, name='delete'),
    
    # Membership management
    path('<slug:slug>/join/', views.join_crew, name='join'),
    path('<slug:slug>/leave/', views.leave_crew, name='leave'),
    path('<slug:slug>/members/', views.crew_members, name='members'),
    path('<slug:slug>/members/<int:user_id>/edit/', views.edit_member, name='edit_member'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    
    # Crew-specific invitation system
    path('<slug:slug>/invite/', views.invite_member, name='invite'),
    
    # Activity feed
    path('<slug:slug>/activity/', views.crew_activity, name='activity'),
    
    # Permission Management (Task 4)
    path('<slug:slug>/permissions/', views.manage_permissions, name='manage_permissions'),
    path('<slug:slug>/permissions/<int:user_id>/edit/', views.edit_member_permissions, name='edit_member_permissions'),
    path('<slug:slug>/permissions/bulk/', views.bulk_permissions, name='bulk_permissions'),
    path('<slug:slug>/permissions/ajax/toggle/', views.ajax_toggle_permission, name='ajax_toggle_permission'),
    
    # Enhanced Member Profiles (Phase 3)
    path('<slug:slug>/member/<int:user_id>/profile/', views.member_profile_detail, name='member_profile_detail'),
    path('<slug:slug>/member/<int:user_id>/permissions/', views.update_member_permissions, name='update_member_permissions'),
]
