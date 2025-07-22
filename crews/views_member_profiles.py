"""
Enhanced member profile view for crew context.
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import Crew, CrewMembership, CrewActivity
from events.models import Event


@login_required
def member_profile_detail(request, slug, user_id):
    """
    AJAX view to get detailed member profile information within crew context.
    """
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Check if requesting user has permission to view member details
    user_membership = crew.get_user_membership(request.user)
    if not user_membership:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        member_membership = crew.memberships.get(user_id=user_id, is_active=True)
    except CrewMembership.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    
    member = member_membership.user
    
    # Get member statistics within crew context
    member_stats = {
        'events_organized': Event.objects.filter(
            organizer=member.profile,
            created_by_crew=crew
        ).count(),
        'events_participated': 0,  # Registration system not implemented yet
        'member_since': member_membership.joined_at,
        'role_duration': timezone.now() - member_membership.joined_at,
    }
    
    # Get recent activity involving this member
    recent_activity = CrewActivity.objects.filter(
        crew=crew,
        target_user=member
    ).select_related('user')[:5]
    
    # Get member's events with this crew
    member_events = Event.objects.filter(
        organizer=member.profile,
        created_by_crew=crew
    ).order_by('-start_date')[:5]
    
    # Get permissions summary
    permissions = member_membership.get_permission_summary()
    
    # Check if requesting user can manage this member
    can_manage_member = (
        user_membership.can_manage() and 
        member_membership.user != request.user
    )
    
    context = {
        'member': member,
        'member_membership': member_membership,
        'crew': crew,
        'member_stats': member_stats,
        'recent_activity': recent_activity,
        'member_events': member_events,
        'permissions': permissions,
        'can_manage_member': can_manage_member,
        'requesting_user': request.user,
    }
    
    # Render the profile content
    profile_html = render_to_string(
        'crews/partials/member_profile_content.html', 
        context, 
        request=request
    )
    
    return JsonResponse({
        'success': True,
        'profile_html': profile_html,
        'member_name': member.get_full_name() or member.username,
        'member_role': member_membership.get_role_display(),
    })


@login_required 
def update_member_permissions(request, slug, user_id):
    """
    AJAX view to update member permissions.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    crew = get_object_or_404(Crew, slug=slug, is_active=True)
    
    # Check if requesting user can delegate permissions
    if not crew.can_delegate_permissions(request.user):
        return JsonResponse({'error': 'Not authorized to manage permissions'}, status=403)
    
    try:
        target_membership = crew.memberships.get(user_id=user_id, is_active=True)
    except CrewMembership.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    
    permission_type = request.POST.get('permission_type')
    action = request.POST.get('action')  # 'grant' or 'revoke'
    
    if permission_type not in ['create', 'edit', 'publish', 'delegate']:
        return JsonResponse({'error': 'Invalid permission type'}, status=400)
    
    if action not in ['grant', 'revoke']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    # Check if delegation is allowed
    requesting_membership = crew.get_user_membership(request.user)
    if not requesting_membership.can_delegate_to_member(target_membership):
        return JsonResponse({'error': 'Cannot delegate to this member'}, status=403)
    
    # Apply the permission change
    if action == 'grant':
        target_membership.grant_permission(permission_type, granted_by=request.user)
        message = f"Granted {permission_type} permission to {target_membership.user.username}"
    else:
        target_membership.revoke_permission(permission_type, revoked_by=request.user)
        message = f"Revoked {permission_type} permission from {target_membership.user.username}"
    
    return JsonResponse({
        'success': True,
        'message': message,
        'new_permissions': target_membership.get_permission_summary()
    })
