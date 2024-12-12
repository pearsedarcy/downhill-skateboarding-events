"""
Views for handling user profile functionality in the downhill skateboarding events application.

This module provides views for displaying and managing user profiles, including their
organized events, attending events, reviews, and favorites.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from events.models import RSVP, Favorite
from .forms import UserProfileForm
from typing import Optional
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.core.exceptions import ValidationError
import base64
from django.core.files.base import ContentFile
import re
import cloudinary.uploader


def user_profile(request, username: Optional[str] = None):
    """
    Display a user's profile page with their events, reviews, and favorites.

    Args:
        request: The HTTP request object
        username: Optional username to view specific profile. If None, shows current user's profile

    Returns:
        Rendered profile page or redirect to login if no user is authenticated

    Raises:
        Http404: If specified username doesn't exist
    """
    if username is None:
        if not request.user.is_authenticated:
            return redirect("account_login")
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    profile = user.profile
    attending_events = profile.attending_events.all()[:9]
    
    # Get RSVP statuses for attending events
    rsvp_statuses = {
        rsvp.event_id: rsvp.status
        for rsvp in RSVP.objects.filter(user=profile, event__in=attending_events)
    }

    context = {
        "profile": profile,
        "organized_events": profile.organized_events.all()[:9],
        "attending_events": attending_events,
        "rsvp_statuses": rsvp_statuses,
        "reviews": profile.reviews.all()[:9],
        "favorites": profile.favorites.all()[:9],
    }
    return render(request, "profiles/user_profile.html", context)


@login_required
def edit_profile(request):
    """
    Handle profile editing for the authenticated user.
    """
    profile = request.user.profile
    
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profiles:my_profile")
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, "profiles/edit_profile.html", {"form": form})


@require_POST
@login_required
def update_profile(request):
    """API endpoint to update profile fields"""
    data = json.loads(request.body)
    profile = request.user.profile
    field = data.get('field')
    value = data.get('value')
    
    if field in ['bio', 'instagram']:
        setattr(profile, field, value)
        profile.save()
        return JsonResponse({'status': 'success'})
    
    elif field == 'username':
        if not re.match(r'^[\w.@+-]+$', value):
            return JsonResponse({
                'status': 'error',
                'message': 'Username may only contain letters, numbers, and @/./+/-/_ characters.'
            }, status=400)
            
        if User.objects.exclude(pk=request.user.pk).filter(username=value).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Username already taken.'
            }, status=400)
            
        request.user.username = value
        request.user.save()
        return JsonResponse({'status': 'success'})
    
    elif field == 'avatar':
        try:
            # Remove header from base64 string
            image_data = value.split(',')[1]
            # Upload directly to Cloudinary
            result = cloudinary.uploader.upload(
                f"data:image/png;base64,{image_data}",
                folder="avatars",
                public_id=f"avatar_{request.user.username}",
                overwrite=True,
                resource_type="image"
            )
            # Update profile with new image URL
            profile.avatar = result['public_id']
            profile.save()
            return JsonResponse({
                'status': 'success',
                'avatar_url': result['secure_url']
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid field'}, status=400)


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