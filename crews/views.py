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
from .forms import CrewForm, CrewMembershipForm, CrewInvitationForm, MemberPermissionForm, BulkPermissionForm
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
@crew_permission_required('edit', crew_param='slug')
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
@crew_permission_required('delegate', crew_param='slug')  # Members need delegate permission to manage other members
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


# ============================================================================
# PERMISSION MANAGEMENT VIEWS (Task 4)
# ============================================================================

@login_required
@crew_permission_required('delegate', crew_param='slug')
def manage_permissions(request, slug):
    """Main permission management dashboard."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    user_membership = crew.get_user_membership(request.user)
    
    # Get all active members with their permissions
    members = crew.memberships.filter(is_active=True).order_by('role', 'user__username')
    
    # Add permission summary for each member
    for member in members:
        member.permissions_summary = {
            'create': member.can_create_events,
            'edit': member.can_edit_events,
            'publish': member.can_publish_events,
            'delegate': member.can_delegate_permissions,
            'total_granted': sum([
                member.can_create_events,
                member.can_edit_events, 
                member.can_publish_events,
                member.can_delegate_permissions
            ])
        }
    
    # Calculate permission statistics
    permission_stats = {
        'can_create_events': sum(1 for m in members if m.can_create_events),
        'can_edit_events': sum(1 for m in members if m.can_edit_events),
        'can_publish_events': sum(1 for m in members if m.can_publish_events),
        'can_delegate_permissions': sum(1 for m in members if m.can_delegate_permissions),
        'total_members': members.count()
    }

    return render(request, 'crews/manage_permissions.html', {
        'crew': crew,
        'user_membership': user_membership,
        'members': members,
        'permission_stats': permission_stats,
        'can_manage_delegation': (user_membership.role == 'OWNER' or 
                                 user_membership.can_delegate_permissions),
    })


@login_required
@crew_permission_required('delegate', crew_param='slug')
def edit_member_permissions(request, slug, user_id):
    """Edit permissions for a specific member."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    member_to_edit = get_object_or_404(CrewMembership, crew=crew, user_id=user_id, is_active=True)
    user_membership = crew.get_user_membership(request.user)
    
    # Cannot edit owner permissions (owners have all permissions by default)
    if member_to_edit.role == 'OWNER':
        messages.error(request, "Cannot modify permissions for crew owners.")
        return redirect('crews:manage_permissions', slug=crew.slug)
    
    # Cannot edit your own permissions  
    if member_to_edit.user == request.user:
        messages.error(request, "Cannot modify your own permissions.")
        return redirect('crews:manage_permissions', slug=crew.slug)
    
    if request.method == 'POST':
        form = MemberPermissionForm(
            request.POST, 
            instance=member_to_edit,
            user_requesting=request.user,
            crew=crew
        )
        if form.is_valid():
            # Track what changed
            original_permissions = {
                'create': member_to_edit.can_create_events,
                'edit': member_to_edit.can_edit_events,
                'publish': member_to_edit.can_publish_events,
                'delegate': member_to_edit.can_delegate_permissions,
            }
            
            updated_member = form.save()
            
            # Log the changes
            changes = []
            new_permissions = {
                'create': updated_member.can_create_events,
                'edit': updated_member.can_edit_events,
                'publish': updated_member.can_publish_events,
                'delegate': updated_member.can_delegate_permissions,
            }
            
            for perm_name, new_value in new_permissions.items():
                if original_permissions[perm_name] != new_value:
                    action = "granted" if new_value else "revoked"
                    changes.append(f"{action} {perm_name}")
            
            if changes:
                change_description = f"Permissions updated for {updated_member.user.username}: {', '.join(changes)}"
                CrewActivity.objects.create(
                    crew=crew,
                    user=request.user,
                    activity_type='PERMISSIONS_UPDATED',
                    description=change_description
                )
                
                messages.success(request, f"Permissions updated for {updated_member.user.username}")
            else:
                messages.info(request, "No changes were made.")
            
            return redirect('crews:manage_permissions', slug=crew.slug)
    else:
        form = MemberPermissionForm(
            instance=member_to_edit,
            user_requesting=request.user,
            crew=crew
        )
    
    return render(request, 'crews/edit_member_permissions.html', {
        'crew': crew,
        'member_to_edit': member_to_edit,
        'user_membership': user_membership,
        'form': form,
    })


@login_required
@crew_permission_required('delegate', crew_param='slug')
def bulk_permissions(request, slug):
    """Bulk permission management interface."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    user_membership = crew.get_user_membership(request.user)
    
    if request.method == 'POST':
        form = BulkPermissionForm(
            request.POST,
            crew=crew,
            user_requesting=request.user
        )
        if form.is_valid():
            members = form.cleaned_data['members']
            action = form.cleaned_data['action']
            permission_type = form.cleaned_data['permission_type']
            reason = form.cleaned_data.get('reason', '')
            
            updated_count = 0
            permission_value = (action == 'grant')
            
            for member in members:
                # Skip owners
                if member.role == 'OWNER':
                    continue
                    
                # Update the specific permission
                current_value = getattr(member, permission_type)
                if current_value != permission_value:
                    setattr(member, permission_type, permission_value)
                    member.save()
                    updated_count += 1
            
            if updated_count > 0:
                # Log the bulk change
                permission_name = form.fields['permission_type'].choices[
                    [choice[0] for choice in form.fields['permission_type'].choices].index(permission_type)
                ][1]
                
                description = f"Bulk {action}: {permission_name} for {updated_count} members"
                if reason:
                    description += f" (Reason: {reason})"
                
                CrewActivity.objects.create(
                    crew=crew,
                    user=request.user,
                    activity_type='BULK_PERMISSIONS_UPDATED',
                    description=description
                )
                
                messages.success(request, f"Updated permissions for {updated_count} members.")
            else:
                messages.info(request, "No changes were made (members already had the selected permission state).")
            
            return redirect('crews:manage_permissions', slug=crew.slug)
    else:
        form = BulkPermissionForm(crew=crew, user_requesting=request.user)
    
    # Get eligible members (all members except owner and current user)
    eligible_members = crew.memberships.filter(
        is_active=True
    ).exclude(
        role='OWNER'
    ).exclude(
        user=request.user
    ).order_by('user__username')
    
    # Get all crew members for copy operations
    crew_members = crew.memberships.filter(is_active=True).order_by('user__username')
    
    return render(request, 'crews/bulk_permissions.html', {
        'crew': crew,
        'user_membership': user_membership,
        'form': form,
        'eligible_members': eligible_members,
        'crew_members': crew_members,
    })


from django.http import JsonResponse

@login_required
@crew_permission_required('delegate', crew_param='slug')
def ajax_toggle_permission(request, slug):
    """AJAX endpoint for quick permission toggling."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    user_membership = crew.get_user_membership(request.user)
    
    try:
        member_id = request.POST.get('member_id')
        permission_type = request.POST.get('permission_type')
        
        member = get_object_or_404(CrewMembership, id=member_id, crew=crew, is_active=True)
        
        # Validation
        if member.role == 'OWNER':
            return JsonResponse({'error': 'Cannot modify owner permissions'}, status=400)
        
        if member.user == request.user:
            return JsonResponse({'error': 'Cannot modify your own permissions'}, status=400)
        
        if permission_type not in ['can_create_events', 'can_edit_events', 'can_publish_events', 'can_delegate_permissions']:
            return JsonResponse({'error': 'Invalid permission type'}, status=400)
        
        # Check delegation permission access
        if (permission_type == 'can_delegate_permissions' and 
            not (user_membership.role == 'OWNER' or user_membership.can_delegate_permissions)):
            return JsonResponse({'error': 'Insufficient permissions'}, status=403)
        
        # Toggle the permission
        current_value = getattr(member, permission_type)
        new_value = not current_value
        setattr(member, permission_type, new_value)
        member.save()
        
        # Log the change
        action = "granted" if new_value else "revoked"
        permission_name = permission_type.replace('can_', '').replace('_', ' ').title()
        
        CrewActivity.objects.create(
            crew=crew,
            user=request.user,
            activity_type='PERMISSION_TOGGLED',
            description=f"{action} {permission_name} for {member.user.username}"
        )
        
        # Calculate updated permission statistics
        members = crew.memberships.filter(is_active=True)
        permission_stats = {
            'can_create_events': sum(1 for m in members if m.can_create_events),
            'can_edit_events': sum(1 for m in members if m.can_edit_events),
            'can_publish_events': sum(1 for m in members if m.can_publish_events),
            'can_delegate_permissions': sum(1 for m in members if m.can_delegate_permissions),
            'total_members': members.count()
        }
        
        return JsonResponse({
            'success': True,
            'new_value': new_value,
            'member_id': member.id,
            'permission_type': permission_type,
            'message': f"{permission_name} {'granted to' if new_value else 'revoked from'} {member.user.username}",
            'permission_stats': permission_stats
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
