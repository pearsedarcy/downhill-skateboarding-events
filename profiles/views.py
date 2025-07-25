"""
Views for handling user profile functionality in the downhill skateboarding events application.

This module provides views for displaying and managing user profiles, including their
organized events, attending events, reviews, and favorites with enhanced privacy controls.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.contrib import messages
from events.models import RSVP, Favorite
from profiles.models import UserProfile, ProfileFollow, ProfileActivity
from .forms import AvatarUploadForm
from typing import Optional
import json
import base64
import re
import cloudinary.uploader


class ProfilePrivacyManager:
    """Handle profile privacy and visibility logic"""
    
    def __init__(self, profile, viewer):
        self.profile = profile
        self.viewer = viewer
    
    def can_view_profile(self):
        """Check if viewer can see the profile"""
        if self.viewer == self.profile.user:
            return True
        
        visibility = self.profile.profile_visibility
        
        if visibility == 'PRIVATE':
            return False
        elif visibility == 'CREWS':
            # Check if they're in the same crew (implement when crews are integrated)
            return self.are_crew_mates()
        elif visibility == 'COMMUNITY':
            return self.viewer.is_authenticated if self.viewer else False
        else:  # PUBLIC
            return True
    
    def are_crew_mates(self):
        """Check if viewer and profile owner are in the same crew"""
        if not self.viewer or not self.viewer.is_authenticated:
            return False
        
        # TODO: Implement crew membership check when crews app is integrated
        # For now, return False
        return False
    
    def filter_profile_data(self, context):
        """Filter profile data based on privacy settings"""
        if not self.can_view_profile():
            return None
        
        # If viewer can see profile, apply field-level privacy
        if self.viewer != self.profile.user:
            # Hide location if show_location is False
            if not self.profile.show_location:
                context['profile'].country = ""
                context['profile'].city = ""
        
        return context


def user_profile(request, username: Optional[str] = None):
    """
    Display a user's profile page with privacy controls and enhanced information.

    Args:
        request: The HTTP request object
        username: Optional username to view specific profile. If None, shows current user's profile

    Returns:
        Rendered profile page, forbidden response, or redirect to login

    Raises:
        Http404: If specified username doesn't exist
    """
    if username is None:
        if not request.user.is_authenticated:
            return redirect("account_login")
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    # Ensure the user has a profile (create if needed due to signal issues)
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    # Check privacy permissions
    privacy_manager = ProfilePrivacyManager(profile, request.user)
    if not privacy_manager.can_view_profile():
        return HttpResponseForbidden(
            "This profile is private. You don't have permission to view it."
        )

    # Get profile events and activities with enhanced data
    organized_events = profile.organized_events.all()[:9]
    attending_events = profile.attending_events.all()[:9]
    user_reviews = profile.reviews.all()[:9] if hasattr(profile, 'reviews') else []
    user_favorites = profile.favorites.all()[:9] if hasattr(profile, 'favorites') else []
    
    # Get RSVP statuses for attending events
    rsvp_statuses = {
        rsvp.event_id: rsvp.status
        for rsvp in RSVP.objects.filter(user=profile, event__in=attending_events)
    } if 'RSVP' in globals() else {}

    # Enhanced context with all new profile features
    context = {
        "profile": profile,
        "user_organized_events": organized_events,
        "user_attending_events": attending_events,
        "user_reviews": user_reviews,
        "user_favorites": user_favorites,
        "rsvp_statuses": rsvp_statuses,
        "can_edit": request.user == user,
        "display_name": profile.get_display_name(),
        "full_name": profile.get_full_name(),
        "location_display": profile.get_location_display(),
        "skating_experience": profile.get_skating_experience_display(),
        "completion_percentage": getattr(profile, 'profile_completion_percentage', 0),
        "remaining_percentage": 100 - getattr(profile, 'profile_completion_percentage', 0),
        "completion_suggestions": getattr(profile, 'get_completion_suggestions', lambda: [])(),
        "is_verified": getattr(profile, 'is_verified', False),
        "verification_badge_type": getattr(profile, 'verification_badge_type', None),
        "social_links": getattr(profile, 'get_social_links', lambda: {})(),
        # Social features
        "follower_count": profile.get_follower_count(),
        "following_count": profile.get_following_count(),
        "is_following": profile.is_followed_by(request.user),
        "recent_activities": profile.get_recent_activities(limit=5),
        "skating_stats": {
            'events_organized': len(organized_events) if organized_events else 0,
            'events_attended': len(attending_events) if attending_events else 0,
            'reviews_given': len(user_reviews) if user_reviews else 0,
            'avg_rating': getattr(profile, 'get_average_rating', lambda: None)(),
        },
        # Form choices for editing
        "skating_style_choices": profile._meta.get_field('skating_style').choices,
        "stance_choices": profile._meta.get_field('stance').choices,
        "profile_visibility_choices": profile._meta.get_field('profile_visibility').choices,
        # Backward compatibility
        "organized_events": organized_events,
        "attending_events": attending_events,
        "reviews": user_reviews,
        "favorites": user_favorites,
    }
    
    # Apply privacy filtering
    context = privacy_manager.filter_profile_data(context)
    if context is None:
        return HttpResponseForbidden("Access denied to this profile.")
    
    return render(request, "profiles/user_profile.html", context)

def users_list(request):
    """
    Display a paginated list of users with search filtering and privacy respect.
    Only shows profiles that are visible to the current user.
    """
    query = request.GET.get('q', '')
    
    # Base queryset - only show profiles based on visibility
    if request.user.is_authenticated:
        # Authenticated users can see PUBLIC and COMMUNITY profiles
        users = UserProfile.objects.filter(
            profile_visibility__in=['PUBLIC', 'COMMUNITY']
        ).order_by('user__username')
    else:
        # Anonymous users can only see PUBLIC profiles
        users = UserProfile.objects.filter(
            profile_visibility='PUBLIC'
        ).order_by('user__username')
    
    # Apply search if query provided
    if query:
        users = users.search(query)
    
    # Add follow status for authenticated users
    if request.user.is_authenticated:
        for profile in users:
            profile.is_followed_by_user = profile.is_followed_by(request.user)
    
    # Paginate results
    paginator = Paginator(users, 12)  # Show 12 users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'profiles/users_list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_users': users.count()
    })

@login_required
def edit_profile_deprecated(request):
    """
    DEPRECATED: Handle profile editing for the authenticated user with enhanced validation.
    This view is deprecated in favor of inline editing via API endpoints.
    """
    profile = request.user.profile
    
    if request.method == "POST":
        # UserProfileForm temporarily disabled to unblock OTP migrations
        form = None
        messages.error(request, "Profile editing is temporarily disabled.")
        return redirect("profiles:my_profile")


@require_POST
@login_required
def update_profile_api(request):
    """Enhanced API endpoint for updating profile fields with better validation"""
    try:
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value', '')
        
        if not field:
            return JsonResponse({'success': False, 'error': 'Field name is required'}, status=400)
        
        profile = request.user.profile
        
        # Define allowed fields for security with validation rules
        field_validations = {
            'bio': {'max_length': 500, 'type': 'text'},
            'display_name': {'max_length': 50, 'type': 'text'},
            'instagram': {'max_length': 100, 'type': 'text'},
            'youtube': {'max_length': 200, 'type': 'url'},
            'website': {'max_length': 200, 'type': 'url'},
            'city': {'max_length': 100, 'type': 'text'},
            'country': {'max_length': 100, 'type': 'text'},
            'skating_style': {'choices': dict(profile._meta.get_field('skating_style').choices), 'type': 'choice'},
            'skill_level': {'min': 1, 'max': 10, 'type': 'integer'},
            'stance': {'choices': dict(profile._meta.get_field('stance').choices), 'type': 'choice'},
            'years_skating': {'min': 0, 'max': 100, 'type': 'integer'},
            'primary_setup': {'max_length': 300, 'type': 'text'},
            'profile_visibility': {'choices': dict(profile._meta.get_field('profile_visibility').choices), 'type': 'choice'},
            'show_real_name': {'type': 'boolean'},
            'show_location': {'type': 'boolean'}
        }
        
        if field not in field_validations:
            return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
        
        validation = field_validations[field]
        
        # Type-specific validation
        if validation['type'] == 'text':
            if 'max_length' in validation and len(str(value)) > validation['max_length']:
                return JsonResponse({
                    'success': False, 
                    'error': f'{field.replace("_", " ").title()} must be {validation["max_length"]} characters or less'
                }, status=400)
        
        elif validation['type'] == 'integer':
            try:
                if value == '' or value is None:
                    value = None
                else:
                    value = int(value)
                    if 'min' in validation and value < validation['min']:
                        return JsonResponse({
                            'success': False, 
                            'error': f'{field.replace("_", " ").title()} must be at least {validation["min"]}'
                        }, status=400)
                    if 'max' in validation and value > validation['max']:
                        return JsonResponse({
                            'success': False, 
                            'error': f'{field.replace("_", " ").title()} cannot exceed {validation["max"]}'
                        }, status=400)
            except ValueError:
                return JsonResponse({'success': False, 'error': f'Invalid {field.replace("_", " ")}'}, status=400)
        
        elif validation['type'] == 'choice':
            if value and value not in validation['choices']:
                return JsonResponse({'success': False, 'error': f'Invalid {field.replace("_", " ")}'}, status=400)
        
        elif validation['type'] == 'boolean':
            value = str(value).lower() in ('true', '1', 'yes', 'on')
        
        elif validation['type'] == 'url':
            if value and not (value.startswith('http://') or value.startswith('https://')):
                return JsonResponse({'success': False, 'error': 'URL must start with http:// or https://'}, status=400)
        
        # Update the field
        setattr(profile, field, value)
        profile.save()
        
        # Recalculate completion
        new_percentage = profile.calculate_completion_percentage()
        
        # Get display value for response
        display_value = value
        if validation['type'] == 'choice' and value:
            display_value = validation['choices'].get(value, value)
        
        return JsonResponse({
            'success': True,
            'field': field,
            'value': value,
            'display_value': display_value,
            'completion_percentage': new_percentage,
            'message': f'{field.replace("_", " ").title()} updated successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required 
def upload_avatar_api(request):
    """API endpoint for avatar uploads"""
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
        
        avatar_file = request.FILES['avatar']
        
        # Validate file type
        if not avatar_file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'File must be an image'}, status=400)
        
        # Validate file size (5MB max)
        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File must be less than 5MB'}, status=400)
        
        profile = request.user.profile
        profile.avatar = avatar_file
        profile.save()
        
        # Recalculate completion
        new_percentage = profile.calculate_completion_percentage()
        
        return JsonResponse({
            'success': True,
            'avatar_url': profile.avatar.url,
            'completion_percentage': new_percentage,
            'message': 'Avatar updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_completion_api(request, user_id):
    """API endpoint to get completion percentage and suggestions"""
    try:
        if request.user.id != int(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        profile = request.user.profile
        completion_percentage = profile.calculate_completion_percentage()
        suggestions = profile.get_completion_suggestions()
        
        return JsonResponse({
            'completion_percentage': completion_percentage,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required  
def test_csrf_api(request):
    """Test endpoint to check CSRF token"""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': 'CSRF token is working!',
            'method': request.method
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Use POST method',
            'method': request.method
        })


@require_POST
@login_required
def remove_favorite(request, favorite_id):
    """Remove an event from user's favorites"""
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user.profile)
    favorite.delete()
    return JsonResponse({'status': 'success'})


@require_POST
@login_required
def update_rsvp(request):
    """Update RSVP status for an event"""
    data = json.loads(request.body)
    event_id = data.get('event_id')
    status = data.get('status')

    if not event_id or not status:
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

    try:
        rsvp, created = RSVP.objects.update_or_create(
            user=request.user.profile,
            event_id=event_id,
            defaults={'status': status}
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@require_POST
@login_required
def delete_profile(request):
    """Delete the user's profile and account"""
    user = request.user
    user.delete()
    return redirect('')


@login_required
def profile_completion_suggestions(request):
    """API endpoint to get profile completion suggestions"""
    profile = request.user.profile
    suggestions = []
    
    # Check various fields and suggest improvements
    if not profile.avatar:
        suggestions.append({
            'field': 'avatar',
            'title': 'Add a profile picture',
            'description': 'Profiles with pictures get 5x more views',
            'points': 15,
            'priority': 'high'
        })
    
    if not profile.bio or len(profile.bio) < 50:
        suggestions.append({
            'field': 'bio',
            'title': 'Write a compelling bio',
            'description': 'Tell others about your skating journey and interests',
            'points': 10,
            'priority': 'high'
        })
    
    if not profile.skating_style:
        suggestions.append({
            'field': 'skating_style',
            'title': 'Add your skating style',
            'description': 'Help others find riders with similar interests',
            'points': 10,
            'priority': 'medium'
        })
    
    if not profile.city or not profile.country:
        suggestions.append({
            'field': 'location',
            'title': 'Add your location',
            'description': 'Connect with local skaters and events',
            'points': 10,
            'priority': 'medium'
        })
    
    if not profile.skill_level:
        suggestions.append({
            'field': 'skill_level',
            'title': 'Set your skill level',
            'description': 'Find events and groups that match your abilities',
            'points': 10,
            'priority': 'medium'
        })
    
    if not profile.stance:
        suggestions.append({
            'field': 'stance',
            'title': 'Select your stance',
            'description': 'Regular, goofy, or switch - let others know your style',
            'points': 5,
            'priority': 'medium'
        })
    
    if not profile.years_skating:
        suggestions.append({
            'field': 'years_skating',
            'title': 'Share your experience',
            'description': 'Let others know how long you\'ve been skating',
            'points': 5,
            'priority': 'low'
        })
    
    if not profile.primary_setup:
        suggestions.append({
            'field': 'primary_setup',
            'title': 'Describe your setup',
            'description': 'Share details about your skateboard setup',
            'points': 10,
            'priority': 'medium'
        })
    
    if not profile.instagram:
        suggestions.append({
            'field': 'instagram',
            'title': 'Add Instagram handle',
            'description': 'Connect your social media for more visibility',
            'points': 5,
            'priority': 'low'
        })
    
    return JsonResponse({
        'current_completion': profile.profile_completion_percentage,
        'suggestions': suggestions,
        'total_possible_points': sum(s['points'] for s in suggestions)
    })


# Social Features: Following System

@require_POST
@login_required
def follow_user(request, user_id):
    """Follow a user"""
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Check if user is trying to follow themselves
        if target_user == request.user:
            return JsonResponse({
                'success': False, 
                'error': 'You cannot follow yourself'
            }, status=400)
        
        # Check if already following
        if ProfileFollow.objects.filter(follower=request.user, following=target_user).exists():
            return JsonResponse({
                'success': False, 
                'error': 'You are already following this user'
            }, status=400)
        
        # Create follow relationship
        follow = ProfileFollow.objects.create(
            follower=request.user,
            following=target_user
        )
        
        # Create activity for the follow action
        ProfileActivity.objects.create(
            user=request.user,
            activity_type='PROFILE_UPDATE',
            description=f'Started following {target_user.profile.get_display_name()}',
            related_object_id=target_user.id,
            related_object_type='user',
            is_public=True
        )
        
        # Get updated counts
        follower_count = target_user.followers.count()
        following_count = request.user.following.count()
        
        return JsonResponse({
            'success': True,
            'action': 'followed',
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You are now following {target_user.profile.get_display_name()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
def unfollow_user(request, user_id):
    """Unfollow a user"""
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Find and delete the follow relationship
        follow = ProfileFollow.objects.filter(
            follower=request.user,
            following=target_user
        ).first()
        
        if not follow:
            return JsonResponse({
                'success': False,
                'error': 'You are not following this user'
            }, status=400)
        
        follow.delete()
        
        # Create activity for the unfollow action
        ProfileActivity.objects.create(
            user=request.user,
            activity_type='PROFILE_UPDATE',
            description=f'Stopped following {target_user.profile.get_display_name()}',
            related_object_id=target_user.id,
            related_object_type='user',
            is_public=False  # Don't make unfollows public
        )
        
        # Get updated counts
        follower_count = target_user.followers.count()
        following_count = request.user.following.count()
        
        return JsonResponse({
            'success': True,
            'action': 'unfollowed',
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You unfollowed {target_user.profile.get_display_name()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def followers_list(request, user_id):
    """Display list of followers for a user"""
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    
    # Check privacy permissions
    privacy_manager = ProfilePrivacyManager(profile, request.user)
    if not privacy_manager.can_view_profile():
        return HttpResponseForbidden("You don't have permission to view this profile.")
    
    # Get followers
    followers = ProfileFollow.objects.filter(following=user).select_related(
        'follower__profile'
    ).order_by('-created_at')
    
    # Paginate
    paginator = Paginator(followers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Add is_following status for each follower
    for follow_obj in page_obj:
        follow_obj.follower.profile.is_following_current_user = ProfileFollow.objects.filter(
            follower=request.user, following=follow_obj.follower
        ).exists()
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'followers_count': followers.count(),
        'list_type': 'followers',
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'profiles/follow_list.html', context)


@login_required
def following_list(request, user_id):
    """Display list of users being followed by a user"""
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    
    # Check privacy permissions
    privacy_manager = ProfilePrivacyManager(profile, request.user)
    if not privacy_manager.can_view_profile():
        return HttpResponseForbidden("You don't have permission to view this profile.")
    
    # Get following
    following = ProfileFollow.objects.filter(follower=user).select_related(
        'following__profile'
    ).order_by('-created_at')
    
    # Paginate
    paginator = Paginator(following, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Add is_following status for each user being followed
    for follow_obj in page_obj:
        follow_obj.following.profile.is_following_current_user = ProfileFollow.objects.filter(
            follower=request.user, following=follow_obj.following
        ).exists()
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'following_count': following.count(),
        'list_type': 'following',
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'profiles/follow_list.html', context)


@login_required
def activity_feed(request):
    """Display activity feed from followed users"""
    profile = request.user.profile
    
    # Get activity feed
    activities = profile.get_activity_feed(limit=50)
    
    # Paginate
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'profile': profile,
        'following_count': request.user.following.count(),
    }
    
    return render(request, 'profiles/activity_feed.html', context)


