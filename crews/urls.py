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
    
    # Crew detail and management
    path('<slug:slug>/', views.crew_detail, name='detail'),
    path('<slug:slug>/edit/', views.edit_crew, name='edit'),
    path('<slug:slug>/delete/', views.delete_crew, name='delete'),
    
    # Membership management
    path('<slug:slug>/join/', views.join_crew, name='join'),
    path('<slug:slug>/leave/', views.leave_crew, name='leave'),
    path('<slug:slug>/members/', views.crew_members, name='members'),
    path('<slug:slug>/members/<int:user_id>/edit/', views.edit_member, name='edit_member'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    
    # Invitation system
    path('<slug:slug>/invite/', views.invite_member, name='invite'),
    path('invitations/', views.my_invitations, name='my_invitations'),
    path('invitations/<int:invitation_id>/accept/', views.accept_invitation, name='accept_invitation'),
    path('invitations/<int:invitation_id>/decline/', views.decline_invitation, name='decline_invitation'),
    
    # Activity feed
    path('<slug:slug>/activity/', views.crew_activity, name='activity'),
]
