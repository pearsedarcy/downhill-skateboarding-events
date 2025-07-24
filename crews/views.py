"""
Views for crew management functionality.

Provides views for creating, managing, and interacting with skateboarding crews.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
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
from .views_member_profiles import member_profile_detail, update_member_permissions


def crew_list(request):
    """Display list of all crews."""
    crews = Crew.objects.filter(is_active=True).order_by('name')
    
    # Add membership info for authenticated users
    if request.user.is_authenticated:
        user_crew_ids = set(
            CrewMembership.objects.filter(
                user=request.user, 
                is_active=True
            ).values_list('crew_id', flat=True)
        )
        for crew in crews:
            crew.user_is_member = crew.id in user_crew_ids
    else:
        for crew in crews:
            crew.user_is_member = False
    
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
            event.user_can_publish = event.can_publish(request.user)
        for event in past_events:
            event.user_can_manage = event.can_manage(request.user)
            event.user_can_publish = event.can_publish(request.user)
    
    # Enhanced crew statistics
    crew_stats = {
        # Member statistics
        'total_members': active_memberships.count(),
        'owner_count': active_memberships.filter(role='OWNER').count(),
        'admin_count': active_memberships.filter(role='ADMIN').count(),
        'member_count': active_memberships.filter(role='MEMBER').count(),
        
        # Growth metrics
        'members_this_month': active_memberships.filter(
            joined_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'members_this_year': active_memberships.filter(
            joined_at__gte=timezone.now() - timedelta(days=365)
        ).count(),
        
        # Event statistics
        'total_events': crew_events.count(),
        'upcoming_events': upcoming_events.count(),
        'past_events': past_events.count(),
        'published_events': crew_events.filter(published=True).count(),
        'events_this_year': crew_events.filter(
            start_date__gte=timezone.now().date().replace(month=1, day=1)
        ).count(),
        
        # Activity metrics
        'recent_activity_count': CrewActivity.objects.filter(
            crew=crew,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'total_activity_count': CrewActivity.objects.filter(crew=crew).count(),
        
        # Engagement metrics
        'avg_events_per_month': 0,
        'crew_age_days': (timezone.now().date() - crew.created_at.date()).days,
        'is_active_crew': False,  # Will calculate below
    }
    
    # Calculate average events per month
    if crew_stats['crew_age_days'] > 0:
        months_active = max(1, crew_stats['crew_age_days'] / 30.44)  # Average days per month
        crew_stats['avg_events_per_month'] = round(crew_stats['total_events'] / months_active, 1)
    
    # Determine if crew is considered "active" (recent activity)
    crew_stats['is_active_crew'] = (
        crew_stats['recent_activity_count'] > 0 or 
        crew_stats['upcoming_events'] > 0 or
        crew_stats['members_this_month'] > 0
    )
    
    # Member role breakdown for chart/display
    crew_stats['role_breakdown'] = [
        {'role': 'Owner', 'count': crew_stats['owner_count'], 'percentage': 0},
        {'role': 'Admin', 'count': crew_stats['admin_count'], 'percentage': 0},
        {'role': 'Member', 'count': crew_stats['member_count'], 'percentage': 0},
    ]
    
    # Calculate percentages
    total_members = crew_stats['total_members']
    if total_members > 0:
        for role_data in crew_stats['role_breakdown']:
            role_data['percentage'] = round((role_data['count'] / total_members) * 100, 1)
    
    # Recent member activity
    recent_members = active_memberships.filter(
        joined_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-joined_at')[:5]
    
    # Crew achievements/milestones
    achievements = []
    if crew_stats['total_members'] >= 10:
        achievements.append({'name': 'Growing Community', 'icon': 'fas fa-users', 'description': '10+ members'})
    if crew_stats['total_events'] >= 5:
        achievements.append({'name': 'Event Organizer', 'icon': 'fas fa-calendar-check', 'description': '5+ events organized'})
    if crew_stats['crew_age_days'] >= 365:
        achievements.append({'name': 'Established Crew', 'icon': 'fas fa-clock', 'description': '1+ years active'})
    if crew.is_verified:
        achievements.append({'name': 'Verified Crew', 'icon': 'fas fa-check-circle', 'description': 'Official verification'})
    if crew_stats['published_events'] >= 3:
        achievements.append({'name': 'Event Publisher', 'icon': 'fas fa-globe', 'description': '3+ published events'})
    
    return render(request, 'crews/crew_detail.html', {
        'crew': crew,
        'can_manage': can_manage,
        'user_membership': user_membership,
        'user_permissions': user_permissions,
        'active_memberships': active_memberships,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'total_events': crew_events.count(),
        'crew_stats': crew_stats,
        'recent_members': recent_members,
        'achievements': achievements,
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
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Check if user is already an active member
    existing_active_membership = crew.memberships.filter(user=request.user, is_active=True).first()
    if existing_active_membership:
        messages.info(request, f"You are already a member of {crew.name}.")
        return redirect('crews:detail', slug=slug)
    
    # Check if user has an inactive membership (previously left)
    existing_inactive_membership = crew.memberships.filter(user=request.user, is_active=False).first()
    
    if existing_inactive_membership:
        # Reactivate the existing membership
        existing_inactive_membership.is_active = True
        existing_inactive_membership.joined_at = timezone.now()  # Update join date
        existing_inactive_membership.save()
        
        membership = existing_inactive_membership
        join_method = 'rejoin'
        welcome_message = f"Welcome back to {crew.name}! You have rejoined the crew."
    else:
        # Create new membership for first-time joiner
        membership = CrewMembership.objects.create(
            crew=crew,
            user=request.user,
            role='MEMBER',
            is_active=True
        )
        join_method = 'direct'
        welcome_message = f"Welcome to {crew.name}! You are now a member of this crew."
    
    # Create activity log
    CrewActivity.objects.create(
        crew=crew,
        activity_type='MEMBER_JOINED',
        user=request.user,
        description=f"{request.user.username} {'rejoined' if join_method == 'rejoin' else 'joined'} {crew.name}",
        metadata={'join_method': join_method}
    )
    
    messages.success(request, welcome_message)
    return redirect('crews:detail', slug=slug)


@login_required
def leave_crew(request, slug):
    """Leave a crew."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Check if user is a member
    membership = crew.memberships.filter(user=request.user, is_active=True).first()
    if not membership:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': f"You are not a member of {crew.name}."
            })
        messages.error(request, f"You are not a member of {crew.name}.")
        return redirect('crews:detail', slug=slug)
    
    # Check if user is the only owner
    if membership.role == 'OWNER':
        other_owners = crew.memberships.filter(role='OWNER', is_active=True).exclude(user=request.user)
        if not other_owners.exists():
            error_msg = "You cannot leave the crew as you are the only owner. Please transfer ownership first or delete the crew."
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            messages.error(request, error_msg)
            return redirect('crews:detail', slug=slug)
    
    # Deactivate membership instead of deleting for historical records
    membership.is_active = False
    membership.save()
    
    # Create activity log
    CrewActivity.objects.create(
        crew=crew,
        activity_type='MEMBER_LEFT',
        user=request.user,
        description=f"{request.user.username} left {crew.name}",
        metadata={'leave_method': 'voluntary'}
    )
    
    success_msg = f"You have left {crew.name}."
    
    # Handle AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'is_member': False,
            'member_count': crew.memberships.filter(is_active=True).count()
        })
    
    messages.success(request, success_msg)
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
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Check if user can invite members
    user_membership = crew.get_user_membership(request.user)
    if not user_membership or not user_membership.can_invite_members:
        messages.error(request, "You don't have permission to invite members to this crew.")
        return redirect('crews:detail', slug=slug)
    
    if request.method == 'POST':
        form = CrewInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.crew = crew
            invitation.inviter = request.user
            
            # Set expiration date (30 days from now)
            from datetime import timedelta
            invitation.expires_at = timezone.now() + timedelta(days=30)
            
            # Check if user already exists
            from django.contrib.auth.models import User
            try:
                existing_user = User.objects.get(email=invitation.invitee_email)
                invitation.invitee_user = existing_user
                
                # Check if user is already a member
                if crew.memberships.filter(user=existing_user, is_active=True).exists():
                    messages.error(request, f"{existing_user.username} is already a member of this crew.")
                    return render(request, 'crews/invite_member.html', {
                        'crew': crew,
                        'form': form,
                        'user_membership': user_membership
                    })
                
                # Check if invitation already exists and is pending
                existing_invitation = crew.invitations.filter(
                    invitee_email=invitation.invitee_email,
                    is_accepted=False,
                    is_declined=False
                ).first()
                
                if existing_invitation and not existing_invitation.is_expired:
                    messages.error(request, f"An invitation to {invitation.invitee_email} is already pending.")
                    return render(request, 'crews/invite_member.html', {
                        'crew': crew,
                        'form': form,
                        'user_membership': user_membership
                    })
                
            except User.DoesNotExist:
                invitation.invitee_user = None
            
            invitation.save()
            
            # Create activity log
            CrewActivity.objects.create(
                crew=crew,
                activity_type='MEMBER_PROMOTED',  # Using this for invitations
                user=request.user,
                target_user=invitation.invitee_user,
                description=f"{request.user.username} invited {invitation.invitee_email} to join {crew.name}",
                metadata={
                    'action': 'invited',
                    'proposed_role': invitation.proposed_role,
                    'invitation_id': invitation.id
                }
            )
            
            # TODO: Send email notification (implement later)
            
            messages.success(request, f"Invitation sent to {invitation.invitee_email}!")
            return redirect('crews:detail', slug=slug)
    else:
        form = CrewInvitationForm()
    
    return render(request, 'crews/invite_member.html', {
        'crew': crew,
        'form': form,
        'user_membership': user_membership
    })


@login_required
def my_invitations(request):
    """Show user's pending crew invitations."""
    # Get invitations by email and by user account
    invitations_by_email = CrewInvitation.objects.filter(
        invitee_email=request.user.email,
        is_accepted=False,
        is_declined=False
    ).select_related('crew', 'inviter')
    
    invitations_by_user = CrewInvitation.objects.filter(
        invitee_user=request.user,
        is_accepted=False,
        is_declined=False
    ).select_related('crew', 'inviter')
    
    # Combine and remove duplicates
    all_invitations = list(invitations_by_email) + list(invitations_by_user)
    seen_crews = set()
    unique_invitations = []
    
    for invitation in all_invitations:
        if invitation.crew.id not in seen_crews:
            seen_crews.add(invitation.crew.id)
            unique_invitations.append(invitation)
    
    # Filter out expired invitations
    pending_invitations = [inv for inv in unique_invitations if not inv.is_expired]
    
    return render(request, 'crews/my_invitations.html', {
        'invitations': pending_invitations
    })


@login_required
def accept_invitation(request, invitation_id):
    """Accept a crew invitation."""
    invitation = get_object_or_404(
        CrewInvitation, 
        id=invitation_id,
        is_accepted=False,
        is_declined=False
    )
    
    # Verify this invitation is for the current user
    if invitation.invitee_user != request.user and invitation.invitee_email != request.user.email:
        messages.error(request, "This invitation is not for you.")
        return redirect('crews:my_invitations')
    
    # Check if invitation has expired
    if invitation.is_expired:
        messages.error(request, "This invitation has expired.")
        return redirect('crews:my_invitations')
    
    # Check if user is already a member
    existing_active_membership = invitation.crew.memberships.filter(user=request.user, is_active=True).first()
    if existing_active_membership:
        messages.error(request, f"You are already a member of {invitation.crew.name}.")
        invitation.is_accepted = True  # Mark as accepted to clean up
        invitation.responded_at = timezone.now()
        invitation.save()
        return redirect('crews:my_invitations')
    
    # Check if user has an inactive membership (previously left)
    existing_inactive_membership = invitation.crew.memberships.filter(user=request.user, is_active=False).first()
    
    if existing_inactive_membership:
        # Reactivate the existing membership with the invited role
        existing_inactive_membership.is_active = True
        existing_inactive_membership.role = invitation.proposed_role
        existing_inactive_membership.invited_by = invitation.inviter
        existing_inactive_membership.joined_at = timezone.now()  # Update join date
        existing_inactive_membership.save()
        
        membership = existing_inactive_membership
        join_method = 'invitation_rejoin'
    else:
        # Create new membership
        membership = CrewMembership.objects.create(
            crew=invitation.crew,
            user=request.user,
            role=invitation.proposed_role,
            invited_by=invitation.inviter,
            is_active=True
        )
        join_method = 'invitation'
    
    # Mark invitation as accepted
    invitation.is_accepted = True
    invitation.responded_at = timezone.now()
    invitation.save()
    
    # Create activity log
    CrewActivity.objects.create(
        crew=invitation.crew,
        activity_type='MEMBER_JOINED',
        user=request.user,
        description=f"{request.user.username} accepted invitation and joined {invitation.crew.name}",
        metadata={
            'join_method': join_method,
            'invited_by': invitation.inviter.username,
            'role': invitation.proposed_role
        }
    )
    
    # Success message
    if join_method == 'invitation_rejoin':
        messages.success(request, f"Welcome back to {invitation.crew.name}! Your membership has been reactivated.")
    else:
        messages.success(request, f"Welcome to {invitation.crew.name}! You are now a {invitation.get_proposed_role_display().lower()}.")
    
    return redirect('crews:detail', slug=invitation.crew.slug)


@login_required
def decline_invitation(request, invitation_id):
    """Decline a crew invitation."""
    invitation = get_object_or_404(
        CrewInvitation, 
        id=invitation_id,
        is_accepted=False,
        is_declined=False
    )
    
    # Verify this invitation is for the current user
    if invitation.invitee_user != request.user and invitation.invitee_email != request.user.email:
        messages.error(request, "This invitation is not for you.")
        return redirect('crews:my_invitations')
    
    # Mark invitation as declined
    invitation.is_declined = True
    invitation.responded_at = timezone.now()
    invitation.save()
    
    # Create activity log (optional - could be considered private)
    CrewActivity.objects.create(
        crew=invitation.crew,
        activity_type='MEMBER_PROMOTED',  # Using this for invitation responses
        user=invitation.inviter,  # Log shows who sent the invitation
        description=f"Invitation to {invitation.invitee_email} was declined",
        metadata={
            'action': 'invitation_declined',
            'invitee_email': invitation.invitee_email
        }
    )
    
    messages.success(request, f"You declined the invitation to join {invitation.crew.name}.")
    return redirect('crews:my_invitations')


def crew_activity(request, slug):
    """Show crew activity feed with filtering and pagination."""
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Get user's membership to determine permissions
    user_membership = None
    can_view_activity = False
    
    if request.user.is_authenticated:
        user_membership = crew.get_user_membership(request.user)
        can_view_activity = user_membership is not None  # Only crew members can view activity
    
    # If user is not a member, redirect to crew detail
    if not can_view_activity:
        from django.contrib import messages
        messages.error(request, "You must be a crew member to view activity.")
        return redirect('crews:detail', slug=crew.slug)
    
    # Get activity with filtering options
    activities = crew.activities.select_related('user', 'target_user')
    
    # Apply filters
    activity_type = request.GET.get('type')
    if activity_type and activity_type in [choice[0] for choice in CrewActivity.ACTIVITY_TYPES]:
        activities = activities.filter(activity_type=activity_type)
    
    # Date filtering
    from datetime import datetime, timedelta
    date_range = request.GET.get('range', '30')  # Default to last 30 days
    if date_range == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif date_range == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif date_range == '90':
        start_date = timezone.now() - timedelta(days=90)
    else:
        start_date = None
    
    if start_date:
        activities = activities.filter(created_at__gte=start_date)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 20)  # 20 activities per page
    page_number = request.GET.get('page')
    page_activities = paginator.get_page(page_number)
    
    # Get activity statistics
    activity_stats = {
        'total_activities': crew.activities.count(),
        'recent_activities': crew.activities.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'activity_types': crew.activities.values('activity_type').annotate(
            count=models.Count('activity_type')
        ).order_by('-count')[:5]
    }
    
    return render(request, 'crews/crew_activity.html', {
        'crew': crew,
        'activities': page_activities,
        'activity_stats': activity_stats,
        'activity_types': CrewActivity.ACTIVITY_TYPES,
        'selected_type': activity_type,
        'selected_range': date_range,
        'user_membership': user_membership,
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
