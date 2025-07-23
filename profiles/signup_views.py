"""
Enhanced signup views that provide a better onboarding experience.

This module contains views for the multi-step signup process and
profile completion flow.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.urls import reverse
from allauth.account.views import SignupView
from profiles.signup_forms import EnhancedSignupForm, ProfileCompletionForm
from profiles.models import UserProfile
import json


class EnhancedSignupView(SignupView):
    """
    Enhanced signup view that uses our custom form with profile fields.
    """
    form_class = EnhancedSignupForm
    template_name = 'account/signup_enhanced.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Join Our Community',
            'page_description': 'Connect with passionate downhill skateboarding enthusiasts',
        })
        return context
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        The actual profile data saving is handled by CustomAccountAdapter.
        """
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request,
            "Welcome to the community! Your account has been created successfully."
        )
        
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        # Add error message for better UX
        messages.error(
            self.request,
            "There were some errors in your signup form. Please check the details below."
        )
        return super().form_invalid(form)


@login_required
def complete_signup(request):
    """
    View for completing profile setup after basic registration.
    
    This view is used when users need to complete their profile
    information after initial signup.
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist (shouldn't happen with signals)
        profile = UserProfile.objects.create(user=request.user)
    
    # Check if profile is already reasonably complete
    completion_percentage = profile.calculate_completion_percentage()
    if completion_percentage >= 70:
        messages.info(request, "Your profile is already well-completed!")
        return redirect('profiles:my_profile')
    
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            
            # Calculate new completion
            new_completion = profile.calculate_completion_percentage()
            
            messages.success(
                request,
                f"Profile updated! Your profile is now {new_completion}% complete."
            )
            
            # Redirect to profile or onboarding next step
            next_url = request.GET.get('next', reverse('profiles:my_profile'))
            return redirect(next_url)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileCompletionForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'completion_percentage': completion_percentage,
        'is_new_user': request.session.get('is_new_signup', False),
        'page_title': 'Complete Your Profile',
    }
    
    # Clear the new signup flag
    request.session.pop('is_new_signup', None)
    
    return render(request, 'profiles/complete_signup.html', context)


@require_http_methods(["GET"])
def signup_step_validation(request):
    """
    AJAX endpoint for validating signup steps in real-time.
    
    This allows for better UX by validating form fields as users progress
    through the multi-step signup process.
    """
    step = request.GET.get('step', '1')
    
    if step == '1':
        # Validate basic account fields
        username = request.GET.get('username', '').strip()
        email = request.GET.get('email', '').strip()
        
        errors = []
        
        if username:
            # Check username availability
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                errors.append({'field': 'username', 'message': 'This username is already taken'})
        
        if email:
            # Basic email validation
            import re
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email):
                errors.append({'field': 'email', 'message': 'Please enter a valid email address'})
        
        return JsonResponse({
            'valid': len(errors) == 0,
            'errors': errors
        })
    
    elif step == '2':
        # Validate profile fields if needed
        skill_level = request.GET.get('skill_level')
        years_skating = request.GET.get('years_skating')
        
        errors = []
        
        if skill_level:
            try:
                level = int(skill_level)
                if level < 1 or level > 10:
                    errors.append({'field': 'skill_level', 'message': 'Skill level must be between 1 and 10'})
            except ValueError:
                errors.append({'field': 'skill_level', 'message': 'Invalid skill level'})
        
        if years_skating:
            try:
                years = int(years_skating)
                if years < 0 or years > 100:
                    errors.append({'field': 'years_skating', 'message': 'Please enter a realistic number of years'})
            except ValueError:
                errors.append({'field': 'years_skating', 'message': 'Invalid number of years'})
        
        return JsonResponse({
            'valid': len(errors) == 0,
            'errors': errors
        })
    
    return JsonResponse({'valid': True, 'errors': []})


@login_required
def onboarding_tour(request):
    """
    Provide an onboarding tour for new users.
    
    This view shows new users around the platform and helps them
    understand key features.
    """
    profile = request.user.profile
    completion_percentage = profile.calculate_completion_percentage()
    
    # Check if user has already seen the tour
    tour_completed = request.session.get('tour_completed', False)
    
    if request.method == 'POST':
        # Mark tour as completed
        request.session['tour_completed'] = True
        
        # Determine next step based on profile completion
        if completion_percentage < 50:
            return redirect('profiles:complete_signup')
        else:
            return redirect('profiles:my_profile')
    
    context = {
        'profile': profile,
        'completion_percentage': completion_percentage,
        'tour_completed': tour_completed,
        'page_title': 'Welcome to the Community!',
        'suggested_actions': profile.get_completion_suggestions() if hasattr(profile, 'get_completion_suggestions') else [],
    }
    
    return render(request, 'profiles/onboarding_tour.html', context)


def signup_success(request):
    """
    Success page shown after successful signup.
    
    This page provides next steps and welcomes the user to the community.
    """
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    profile = request.user.profile
    completion_percentage = profile.calculate_completion_percentage()
    
    context = {
        'profile': profile,
        'completion_percentage': completion_percentage,
        'is_new_user': True,
        'page_title': 'Welcome to the Community!',
        'next_steps': [
            {
                'title': 'Complete Your Profile',
                'description': 'Add more details to connect with fellow riders',
                'url': reverse('profiles:complete_signup'),
                'icon': 'fas fa-user-edit',
                'completed': completion_percentage >= 70
            },
            {
                'title': 'Explore Events',
                'description': 'Discover skateboarding events in your area',
                'url': reverse('events:event_list'),
                'icon': 'fas fa-calendar-alt',
                'completed': False
            },
            {
                'title': 'Join Community',
                'description': 'Connect with other riders and share experiences',
                'url': reverse('profiles:users_list'),
                'icon': 'fas fa-users',
                'completed': False
            }
        ]
    }
    
    return render(request, 'profiles/signup_success.html', context)
