"""
Permission checking infrastructure for crew-based permissions.

Provides decorators, mixins, and utility functions for verifying crew-based 
permissions throughout the application, particularly for event management.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

from .models import Crew, CrewMembership


# Permission Exception Classes
class CrewPermissionError(PermissionDenied):
    """Base exception for crew permission errors."""
    pass


class CrewNotFoundError(Http404):
    """Exception when crew is not found or user is not a member."""
    pass


class InsufficientPermissionError(CrewPermissionError):
    """Exception when user lacks required crew permission."""
    pass


# Utility Functions
def get_user_crew_membership(user, crew_slug_or_id):
    """
    Get user's active membership in a crew.
    
    Args:
        user: The user to check
        crew_slug_or_id: Either crew slug or crew ID
        
    Returns:
        CrewMembership: Active membership if found
        
    Raises:
        CrewNotFoundError: If crew not found or user not a member
    """
    if not user.is_authenticated:
        raise CrewNotFoundError("User must be authenticated")
    
    # Try to get crew by slug first, then by ID
    try:
        if isinstance(crew_slug_or_id, str) and not crew_slug_or_id.isdigit():
            crew = get_object_or_404(Crew, slug=crew_slug_or_id)
        else:
            crew = get_object_or_404(Crew, pk=crew_slug_or_id)
    except Http404:
        raise CrewNotFoundError(f"Crew not found: {crew_slug_or_id}")
    
    membership = crew.get_user_membership(user)
    if not membership:
        raise CrewNotFoundError(f"User is not an active member of crew: {crew.name}")
    
    return membership


def check_crew_permission(user, crew_slug_or_id, permission_type):
    """
    Check if user has specific crew permission.
    
    Args:
        user: The user to check
        crew_slug_or_id: Either crew slug or crew ID
        permission_type: 'create', 'edit', 'publish', or 'delegate'
        
    Returns:
        bool: True if user has permission
        
    Raises:
        CrewNotFoundError: If crew not found or user not a member
    """
    membership = get_user_crew_membership(user, crew_slug_or_id)
    return membership.has_event_permission(permission_type)


def require_crew_permission(user, crew_slug_or_id, permission_type, raise_exception=True):
    """
    Require user to have specific crew permission.
    
    Args:
        user: The user to check
        crew_slug_or_id: Either crew slug or crew ID
        permission_type: 'create', 'edit', 'publish', or 'delegate'
        raise_exception: Whether to raise exception if permission denied
        
    Returns:
        bool: True if user has permission
        
    Raises:
        InsufficientPermissionError: If user lacks permission (when raise_exception=True)
        CrewNotFoundError: If crew not found or user not a member
    """
    has_permission = check_crew_permission(user, crew_slug_or_id, permission_type)
    
    if not has_permission and raise_exception:
        membership = get_user_crew_membership(user, crew_slug_or_id)
        raise InsufficientPermissionError(
            f"User '{user.username}' lacks '{permission_type}' permission in crew '{membership.crew.name}'"
        )
    
    return has_permission


# View Decorators
def crew_permission_required(permission_type, crew_param='crew_slug', login_url=None, 
                           redirect_on_error=None, message_on_error=None):
    """
    Decorator to require crew permission for function-based views.
    
    Args:
        permission_type (str): Required permission ('create', 'edit', 'publish', 'delegate')
        crew_param (str): Parameter name containing crew slug/ID (default: 'crew_slug')
        login_url (str): URL to redirect unauthenticated users
        redirect_on_error (str): URL to redirect on permission error
        message_on_error (str): Message to show on permission error
        
    Usage:
        @crew_permission_required('create')
        def create_event(request, crew_slug):
            # View logic here
            pass
            
        @crew_permission_required('edit', crew_param='crew_id')
        def edit_event(request, crew_id, event_id):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            # Get crew identifier from URL parameters
            crew_identifier = kwargs.get(crew_param)
            if not crew_identifier:
                raise CrewNotFoundError(f"Missing crew parameter: {crew_param}")
            
            try:
                # Check permission
                require_crew_permission(request.user, crew_identifier, permission_type)
                
                # Permission granted, proceed with view
                return view_func(request, *args, **kwargs)
                
            except CrewNotFoundError:
                # Crew not found or user not a member
                if redirect_on_error:
                    if message_on_error:
                        messages.error(request, message_on_error)
                    return redirect(redirect_on_error)
                raise Http404("Crew not found or access denied")
                
            except InsufficientPermissionError:
                # User lacks permission
                if redirect_on_error:
                    if message_on_error:
                        messages.error(request, message_on_error)
                    else:
                        messages.error(
                            request, 
                            f"You don't have permission to {permission_type} events for this crew."
                        )
                    return redirect(redirect_on_error)
                raise PermissionDenied(f"Insufficient crew permission: {permission_type}")
        
        return _wrapped_view
    return decorator


# Convenience decorators for common permissions
def crew_create_permission_required(crew_param='crew_slug', **kwargs):
    """Decorator requiring crew event creation permission."""
    return crew_permission_required('create', crew_param, **kwargs)


def crew_edit_permission_required(crew_param='crew_slug', **kwargs):
    """Decorator requiring crew event editing permission."""
    return crew_permission_required('edit', crew_param, **kwargs)


def crew_publish_permission_required(crew_param='crew_slug', **kwargs):
    """Decorator requiring crew event publishing permission."""
    return crew_permission_required('publish', crew_param, **kwargs)


def crew_delegate_permission_required(crew_param='crew_slug', **kwargs):
    """Decorator requiring crew permission delegation rights."""
    return crew_permission_required('delegate', crew_param, **kwargs)


# Class-based View Mixins
class CrewPermissionMixin:
    """
    Mixin for class-based views requiring crew permissions.
    
    Attributes:
        required_crew_permission (str): Required permission type
        crew_url_kwarg (str): URL parameter containing crew slug/ID
        permission_denied_message (str): Message to show on permission denial
        permission_denied_url (str): URL to redirect on permission denial
    
    Usage:
        class CreateEventView(CrewPermissionMixin, CreateView):
            required_crew_permission = 'create'
            crew_url_kwarg = 'crew_slug'
            # ... rest of view
    """
    required_crew_permission = None
    crew_url_kwarg = 'crew_slug'
    permission_denied_message = None
    permission_denied_url = None
    
    def dispatch(self, request, *args, **kwargs):
        """Check permission before dispatching to view method."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Get crew identifier
        crew_identifier = self.get_crew_identifier()
        if not crew_identifier:
            raise CrewNotFoundError(f"Missing crew parameter: {self.crew_url_kwarg}")
        
        # Check permission
        try:
            self.check_crew_permission(request.user, crew_identifier)
        except (CrewNotFoundError, InsufficientPermissionError) as e:
            return self.handle_permission_denied(e)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_crew_identifier(self):
        """Get crew identifier from URL kwargs."""
        return self.kwargs.get(self.crew_url_kwarg)
    
    def get_required_permission(self):
        """Get the required permission type."""
        if self.required_crew_permission is None:
            raise NotImplementedError(
                "CrewPermissionMixin requires 'required_crew_permission' to be set"
            )
        return self.required_crew_permission
    
    def check_crew_permission(self, user, crew_identifier):
        """Check if user has required crew permission."""
        permission_type = self.get_required_permission()
        require_crew_permission(user, crew_identifier, permission_type)
    
    def get_crew_membership(self):
        """Get current user's crew membership."""
        crew_identifier = self.get_crew_identifier()
        return get_user_crew_membership(self.request.user, crew_identifier)
    
    def get_crew(self):
        """Get the crew object."""
        return self.get_crew_membership().crew
    
    def handle_permission_denied(self, exception):
        """Handle permission denied scenarios."""
        if self.permission_denied_url:
            if self.permission_denied_message:
                messages.error(self.request, self.permission_denied_message)
            elif isinstance(exception, InsufficientPermissionError):
                messages.error(
                    self.request, 
                    f"You don't have permission to {self.get_required_permission()} events for this crew."
                )
            return redirect(self.permission_denied_url)
        
        # Default handling
        if isinstance(exception, CrewNotFoundError):
            raise Http404("Crew not found or access denied")
        else:
            raise PermissionDenied(str(exception))
    
    def handle_no_permission(self):
        """Handle unauthenticated users."""
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(self.request.get_full_path())


# Specific permission mixins
class CrewCreatePermissionMixin(CrewPermissionMixin):
    """Mixin requiring crew event creation permission."""
    required_crew_permission = 'create'


class CrewEditPermissionMixin(CrewPermissionMixin):
    """Mixin requiring crew event editing permission."""
    required_crew_permission = 'edit'


class CrewPublishPermissionMixin(CrewPermissionMixin):
    """Mixin requiring crew event publishing permission."""
    required_crew_permission = 'publish'


class CrewDelegatePermissionMixin(CrewPermissionMixin):
    """Mixin requiring crew permission delegation rights."""
    required_crew_permission = 'delegate'


# Context processors and template utilities
def get_user_crew_permissions(user, crew_slug_or_id):
    """
    Get user's permission summary for a crew (for use in templates).
    
    Args:
        user: The user to check
        crew_slug_or_id: Either crew slug or crew ID
        
    Returns:
        dict: Permission summary or empty dict if no access
    """
    try:
        membership = get_user_crew_membership(user, crew_slug_or_id)
        return membership.get_permission_summary()
    except (CrewNotFoundError, InsufficientPermissionError):
        return {
            'create': False,
            'edit': False,
            'publish': False,
            'delegate': False,
            'role_based': False,
        }
