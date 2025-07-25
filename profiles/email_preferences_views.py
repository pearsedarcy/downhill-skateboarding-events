"""
Email preference management views for users to control their communication settings.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from profiles.models import UserProfile
from profiles.email_service import email_service


@login_required
@require_http_methods(['GET', 'POST'])
def email_preferences(request):
    """
    View for users to manage their email communication preferences.
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update email preferences
        profile.email_event_notifications = request.POST.get('email_event_notifications') == 'on'
        profile.email_community_news = request.POST.get('email_community_news') == 'on'
        profile.email_newsletter = request.POST.get('email_newsletter') == 'on'
        profile.email_crew_invites = request.POST.get('email_crew_invites') == 'on'
        profile.email_marketing = request.POST.get('email_marketing') == 'on'
        
        profile.save()
        
        messages.success(request, 'Your email preferences have been updated successfully!')
        return redirect('profiles:email_preferences')
    
    # Get email statistics for context
    email_stats = email_service.get_email_stats()
    
    context = {
        'profile': profile,
        'email_stats': email_stats,
        'page_title': 'Email Preferences',
    }
    
    return render(request, 'profiles/email_preferences.html', context)


@login_required
def unsubscribe_all(request):
    """
    Unsubscribe user from all marketing emails but keep essential notifications.
    """
    if request.method == 'POST':
        profile = request.user.profile
        
        # Keep essential notifications but disable marketing
        profile.email_marketing = False
        profile.email_newsletter = False
        profile.save()
        
        messages.success(
            request, 
            'You have been unsubscribed from promotional emails. '
            'You will still receive important account and event notifications.'
        )
        
        return redirect('profiles:email_preferences')
    
    return render(request, 'profiles/unsubscribe_confirm.html', {
        'page_title': 'Unsubscribe from Emails'
    })
