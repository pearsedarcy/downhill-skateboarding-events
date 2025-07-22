"""
Views for crew management functionality.

Provides views for creating, managing, and interacting with skateboarding crews.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import models
from datetime import timedelta
from .models import Crew, CrewMembership, CrewInvitation, CrewActivity
from .forms import CrewForm, CrewMembershipForm, CrewInvitationForm
from .permissions import (
    crew_permission_required, 
    CrewPermissionMixin,
    check_crew_permission,
    require_crew_permission,
    CrewNotFoundError,
    InsufficientPermissionError
)


def crew_list(request):
    """Display list of all crews."""
    crews = Crew.objects.filter(is_active=True).order_by('name')
    return render(request, 'crews/crew_list.html', {
        'crews': crews
    })


def crew_detail(request, slug):
    """Display crew detail page."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Get user's membership to determine permissions
    user_membership = None
    can_manage = False
    user_permissions = {}
    
    if request.user.is_authenticated:
        user_membership = crew.get_user_membership(request.user)
        if user_membership:
            # User is a member - get all permissions
            user_permissions = {
                'create': user_membership.has_event_permission('create'),
                'edit': user_membership.has_event_permission('edit'), 
                'publish': user_membership.has_event_permission('publish'),
                'delegate': user_membership.has_event_permission('delegate'),
                'manage_crew': user_membership.can_manage(),
            }
            can_manage = user_permissions['manage_crew']
        else:
            # User is authenticated but not a member
            user_permissions = {
                'create': False, 'edit': False, 'publish': False, 
                'delegate': False, 'manage_crew': False
            }
    else:
        # User is not authenticated
        user_membership = None
        user_permissions = {
            'create': False, 'edit': False, 'publish': False, 
            'delegate': False, 'manage_crew': False
        }
    
    active_memberships = crew.memberships.filter(is_active=True).order_by('role', 'joined_at')
    
    # Get events created by this crew
    from events.models import Event
    from django.utils import timezone
    
    crew_events = Event.objects.filter(
        created_by_crew=crew
    ).order_by('-start_date')
    
    # Separate upcoming and past events
    now = timezone.now().date()
    upcoming_events = crew_events.filter(start_date__gte=now)
    past_events = crew_events.filter(start_date__lt=now)
    
    # Add event management permissions for each event
    if request.user.is_authenticated:
        for event in upcoming_events:
            event.user_can_manage = event.can_manage(request.user)
        for event in past_events:
            event.user_can_manage = event.can_manage(request.user)
    
    return render(request, 'crews/crew_detail.html', {
        'crew': crew,
        'can_manage': can_manage,
        'user_membership': user_membership,
        'user_permissions': user_permissions,
        'active_memberships': active_memberships,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'total_events': crew_events.count(),
    })


@login_required
def create_crew(request):
    """Create a new crew."""
    if request.method == 'POST':
        form = CrewForm(request.POST, request.FILES)
        if form.is_valid():
            crew = form.save(commit=False)
            crew.save()
            
            # Create membership for the creator as owner
            CrewMembership.objects.create(
                crew=crew,
                user=request.user,
                role='OWNER',
                is_active=True
            )
            
            # Create activity record
            CrewActivity.objects.create(
                crew=crew,
                activity_type='CREW_UPDATED',
                user=request.user,
                description=f'{request.user.username} created the crew'
            )
            
            messages.success(request, f'Crew "{crew.name}" created successfully!')
            return redirect('crews:detail', slug=crew.slug)
        else:
            # Add debugging to see what validation errors we have
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                print(f"Field {field}: {errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CrewForm()
    
    return render(request, 'crews/create_crew.html', {
        'form': form
    })


@login_required  
@crew_permission_required('edit')
def edit_crew(request, slug):
    """Edit crew details."""
    crew = get_object_or_404(Crew, slug=slug)
    
    if request.method == 'POST':
        form = CrewForm(request.POST, request.FILES, instance=crew)
        if form.is_valid():
            updated_crew = form.save()
            
            # Create activity record
            CrewActivity.objects.create(
                crew=updated_crew,
                activity_type='CREW_UPDATED',
                user=request.user,
                description=f'{request.user.username} updated crew details'
            )
            
            messages.success(request, f'Crew "{updated_crew.name}" updated successfully!')
            return redirect('crews:detail', slug=updated_crew.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CrewForm(instance=crew)
    
    return render(request, 'crews/edit_crew.html', {
        'form': form,
        'crew': crew
    })


@login_required
def delete_crew(request, slug):
    """
    Delete a crew.
    Only crew owners can delete crews.
    """
    crew = get_object_or_404(Crew, slug=slug)
    
    # Check if user is the owner using new permission system
    try:
        user_membership = crew.get_user_membership(request.user)
        if user_membership.role != 'OWNER':
            messages.error(request, "Only crew owners can delete crews.")
            return redirect('crews:detail', slug=crew.slug)
    except CrewMembership.DoesNotExist:
        messages.error(request, "Only crew owners can delete crews.")
        return redirect('crews:detail', slug=crew.slug)
    
    if request.method == 'POST':
        # Verify the user typed the crew name correctly
        confirm_name = request.POST.get('confirm_name', '')
        if confirm_name != crew.name:
            messages.error(request, "Please type the crew name exactly to confirm deletion.")
            return render(request, 'crews/delete_crew.html', {
                'crew': crew,
                'user_membership': user_membership,
            })
        
        crew_name = crew.name
        crew.delete()
        
        messages.success(request, f'Crew "{crew_name}" has been deleted successfully.')
        return redirect('crews:list')
    
    return render(request, 'crews/delete_crew.html', {
        'crew': crew,
        'user_membership': user_membership,
    })


@login_required
def join_crew(request, slug):
    """Join a crew."""
    # TODO: Implement crew joining
    return redirect('crews:detail', slug=slug)


@login_required
def leave_crew(request, slug):
    """Leave a crew."""
    # TODO: Implement leaving crew
    return redirect('crews:detail', slug=slug)


@login_required
def crew_members(request, slug):
    """Display crew members with management options."""
    crew = get_object_or_404(Crew, slug=slug)
    user_membership = crew.memberships.filter(user=request.user).first()
    
    # Get all memberships ordered by role hierarchy
    role_order = {'owner': 1, 'admin': 2, 'event_manager': 3, 'member': 4}
    memberships = crew.memberships.select_related('user').order_by(
        models.Case(
            *[models.When(role=role, then=order) for role, order in role_order.items()],
            output_field=models.IntegerField()
        ),
        'joined_at'
    )
    
    return render(request, 'crews/crew_members.html', {
        'crew': crew,
        'memberships': memberships,
        'user_membership': user_membership,
    })


@login_required
def edit_member(request, slug, user_id):
    """Edit a crew member's role and permissions."""
    crew = get_object_or_404(Crew, slug=slug)
    member_to_edit = get_object_or_404(CrewMembership, crew=crew, user_id=user_id)
    user_membership = crew.memberships.filter(user=request.user).first()
    
    # Check permissions - only owners and admins can edit member roles
    if not user_membership or not user_membership.can_manage():
        messages.error(request, "You don't have permission to edit member roles.")
        return redirect('crews:members', slug=crew.slug)
    
    # Owners cannot be edited by anyone except themselves
    if member_to_edit.role == 'OWNER' and request.user != member_to_edit.user:
        messages.error(request, "Crew owners can only edit their own role.")
        return redirect('crews:members', slug=crew.slug)
    
    # Admins cannot promote members to owner
    if user_membership.role == 'ADMIN' and request.POST.get('role') == 'OWNER':
        messages.error(request, "Only current owners can transfer ownership.")
        return redirect('crews:members', slug=crew.slug)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(CrewMembership.ROLE_CHOICES):
            old_role = member_to_edit.role
            member_to_edit.role = new_role
            member_to_edit.save()
            
            # Log the activity
            CrewActivity.objects.create(
                crew=crew,
                user=request.user,
                activity_type='member_role_changed',
                description=f'{member_to_edit.user.get_full_name() or member_to_edit.user.username} role changed from {old_role} to {new_role}'
            )
            
            messages.success(request, f"Updated {member_to_edit.user.get_full_name() or member_to_edit.user.username}'s role to {new_role}.")
        else:
            messages.error(request, "Invalid role selected.")
        
        return redirect('crews:members', slug=crew.slug)
    
    return render(request, 'crews/edit_member.html', {
        'crew': crew,
        'member_to_edit': member_to_edit,
        'user_membership': user_membership,
        'role_choices': CrewMembership.ROLE_CHOICES,
    })


@login_required
@crew_permission_required('delegate')  # Members need delegate permission to manage other members
def remove_member(request, slug, user_id):
    """Remove a member from the crew."""
    crew = get_object_or_404(Crew, slug=slug)
    member_to_remove = get_object_or_404(CrewMembership, crew=crew, user_id=user_id)
    user_membership = crew.get_user_membership(request.user)
    
    # Cannot remove crew owner
    if member_to_remove.role == 'OWNER':
        messages.error(request, "Cannot remove crew owner. Transfer ownership first.")
        return redirect('crews:members', slug=crew.slug)
    
    # Admins cannot remove other admins unless they're owner
    if (user_membership.role == 'ADMIN' and 
        member_to_remove.role == 'ADMIN' and 
        member_to_remove.user != request.user):
        messages.error(request, "Admins cannot remove other admins.")
        return redirect('crews:members', slug=crew.slug)
    
    if request.method == 'POST':
        # Verify the user typed the username correctly
        confirm_username = request.POST.get('confirm_username', '')
        if confirm_username != member_to_remove.user.username:
            messages.error(request, "Please type the username exactly to confirm removal.")
            return render(request, 'crews/remove_member.html', {
                'crew': crew,
                'member_to_remove': member_to_remove,
                'user_membership': user_membership,
            })
        
        member_name = member_to_remove.user.get_full_name() or member_to_remove.user.username
        removal_reason = request.POST.get('removal_reason', '').strip()
        
        # Delete the membership
        member_to_remove.delete()
        
        # Log the activity
        description = f'{member_name} was removed from the crew'
        if removal_reason:
            description += f' (Reason: {removal_reason})'
        
        CrewActivity.objects.create(
            crew=crew,
            user=request.user,
            activity_type='member_removed',
            description=description
        )
        
        messages.success(request, f"{member_name} has been removed from the crew.")
        return redirect('crews:members', slug=crew.slug)
    
    return render(request, 'crews/remove_member.html', {
        'crew': crew,
        'member_to_remove': member_to_remove,
        'user_membership': user_membership,
    })


@login_required
def invite_member(request, slug):
    """Invite someone to join the crew."""
    # TODO: Implement invitation system
    return render(request, 'crews/invite_member.html')


@login_required
def my_invitations(request):
    """Show user's pending crew invitations."""
    # TODO: Implement invitation listing
    return render(request, 'crews/my_invitations.html')


@login_required
def accept_invitation(request, invitation_id):
    """Accept a crew invitation."""
    # TODO: Implement invitation acceptance
    return redirect('crews:my_invitations')


@login_required
def decline_invitation(request, invitation_id):
    """Decline a crew invitation."""
    # TODO: Implement invitation decline
    return redirect('crews:my_invitations')


def crew_activity(request, slug):
    """Show crew activity feed."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    return render(request, 'crews/crew_activity.html', {
        'crew': crew
    })
