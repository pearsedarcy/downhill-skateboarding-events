"""
Tests for crew permission checking infrastructure.

Tests decorators, mixins, and utility functions for crew permissions.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from unittest.mock import Mock, patch

from crews.models import Crew, CrewMembership
from crews.permissions import (
    CrewPermissionError, CrewNotFoundError, InsufficientPermissionError,
    get_user_crew_membership, check_crew_permission, require_crew_permission,
    crew_permission_required, CrewPermissionMixin,
    get_user_crew_permissions
)


class PermissionUtilitiesTestCase(TestCase):
    """Test cases for permission utility functions."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.owner = User.objects.create_user('owner', 'owner@test.com', 'password')
        self.member = User.objects.create_user('member', 'member@test.com', 'password')
        self.outsider = User.objects.create_user('outsider', 'outsider@test.com', 'password')
        
        # Create test crew
        self.crew = Crew.objects.create(
            name='Test Crew',
            slug='test-crew',
            description='A test crew for permissions testing'
        )
        
        # Create memberships
        self.owner_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.owner,
            role='OWNER'
        )
        
        self.member_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.member,
            role='MEMBER'
        )
    
    def test_get_user_crew_membership_by_slug(self):
        """Test getting membership by crew slug."""
        membership = get_user_crew_membership(self.owner, 'test-crew')
        self.assertEqual(membership, self.owner_membership)
        
        membership = get_user_crew_membership(self.member, 'test-crew')
        self.assertEqual(membership, self.member_membership)
    
    def test_get_user_crew_membership_by_id(self):
        """Test getting membership by crew ID."""
        membership = get_user_crew_membership(self.owner, self.crew.id)
        self.assertEqual(membership, self.owner_membership)
    
    def test_get_user_crew_membership_not_member(self):
        """Test getting membership for non-member."""
        with self.assertRaises(CrewNotFoundError):
            get_user_crew_membership(self.outsider, 'test-crew')
    
    def test_get_user_crew_membership_unauthenticated(self):
        """Test getting membership for unauthenticated user."""
        anonymous = AnonymousUser()
        with self.assertRaises(CrewNotFoundError):
            get_user_crew_membership(anonymous, 'test-crew')
    
    def test_get_user_crew_membership_invalid_crew(self):
        """Test getting membership for non-existent crew."""
        with self.assertRaises(CrewNotFoundError):
            get_user_crew_membership(self.owner, 'nonexistent-crew')
    
    def test_check_crew_permission_owner(self):
        """Test permission checking for owner."""
        self.assertTrue(check_crew_permission(self.owner, 'test-crew', 'create'))
        self.assertTrue(check_crew_permission(self.owner, 'test-crew', 'edit'))
        self.assertTrue(check_crew_permission(self.owner, 'test-crew', 'publish'))
        self.assertTrue(check_crew_permission(self.owner, 'test-crew', 'delegate'))
    
    def test_check_crew_permission_member_no_permissions(self):
        """Test permission checking for member without permissions."""
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'create'))
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'edit'))
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'publish'))
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'delegate'))
    
    def test_check_crew_permission_member_with_permissions(self):
        """Test permission checking for member with specific permissions."""
        self.member_membership.can_create_events = True
        self.member_membership.can_publish_events = True
        self.member_membership.save()
        
        self.assertTrue(check_crew_permission(self.member, 'test-crew', 'create'))
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'edit'))
        self.assertTrue(check_crew_permission(self.member, 'test-crew', 'publish'))
        self.assertFalse(check_crew_permission(self.member, 'test-crew', 'delegate'))
    
    def test_require_crew_permission_success(self):
        """Test requiring permission when user has it."""
        self.assertTrue(require_crew_permission(self.owner, 'test-crew', 'create'))
    
    def test_require_crew_permission_failure_with_exception(self):
        """Test requiring permission when user lacks it (with exception)."""
        with self.assertRaises(InsufficientPermissionError):
            require_crew_permission(self.member, 'test-crew', 'create')
    
    def test_require_crew_permission_failure_without_exception(self):
        """Test requiring permission when user lacks it (without exception)."""
        result = require_crew_permission(self.member, 'test-crew', 'create', raise_exception=False)
        self.assertFalse(result)
    
    def test_get_user_crew_permissions_with_access(self):
        """Test getting permission summary for user with access."""
        permissions = get_user_crew_permissions(self.owner, 'test-crew')
        expected = {
            'create': True,
            'edit': True,
            'publish': True,
            'delegate': True,
            'role_based': True,
        }
        self.assertEqual(permissions, expected)
    
    def test_get_user_crew_permissions_without_access(self):
        """Test getting permission summary for user without access."""
        permissions = get_user_crew_permissions(self.outsider, 'test-crew')
        expected = {
            'create': False,
            'edit': False,
            'publish': False,
            'delegate': False,
            'role_based': False,
        }
        self.assertEqual(permissions, expected)


class PermissionDecoratorsTestCase(TestCase):
    """Test cases for permission decorators."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.owner = User.objects.create_user('owner', 'owner@test.com', 'password')
        self.member = User.objects.create_user('member', 'member@test.com', 'password')
        
        # Create test crew
        self.crew = Crew.objects.create(
            name='Test Crew',
            slug='test-crew',
            description='A test crew for permissions testing'
        )
        
        # Create memberships
        CrewMembership.objects.create(crew=self.crew, user=self.owner, role='OWNER')
        CrewMembership.objects.create(crew=self.crew, user=self.member, role='MEMBER')
    
    def add_session_and_messages(self, request):
        """Add session and messages support to request."""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        request._messages = messages
        return request
    
    def test_crew_permission_required_success(self):
        """Test decorator when user has permission."""
        @crew_permission_required('create')
        def test_view(request, crew_slug):
            return f"Success for {crew_slug}"
        
        request = self.factory.get('/test/')
        request.user = self.owner
        request = self.add_session_and_messages(request)
        
        result = test_view(request, crew_slug='test-crew')
        self.assertEqual(result, "Success for test-crew")
    
    def test_crew_permission_required_insufficient_permission(self):
        """Test decorator when user lacks permission."""
        @crew_permission_required('create')
        def test_view(request, crew_slug):
            return f"Success for {crew_slug}"
        
        request = self.factory.get('/test/')
        request.user = self.member
        request = self.add_session_and_messages(request)
        
        with self.assertRaises(PermissionDenied):
            test_view(request, crew_slug='test-crew')
    
    def test_crew_permission_required_unauthenticated(self):
        """Test decorator with unauthenticated user."""
        @crew_permission_required('create')
        def test_view(request, crew_slug):
            return f"Success for {crew_slug}"
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request = self.add_session_and_messages(request)
        
        # This should redirect to login (we'll just check it doesn't crash)
        with patch('crews.permissions.redirect_to_login') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            result = test_view(request, crew_slug='test-crew')
            mock_redirect.assert_called_once()
    
    def test_crew_permission_required_with_redirect(self):
        """Test decorator with custom redirect on error."""
        @crew_permission_required('create', redirect_on_error='/crews/', 
                                message_on_error='Custom error message')
        def test_view(request, crew_slug):
            return f"Success for {crew_slug}"
        
        request = self.factory.get('/test/')
        request.user = self.member
        request = self.add_session_and_messages(request)
        
        with patch('crews.permissions.redirect') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            result = test_view(request, crew_slug='test-crew')
            mock_redirect.assert_called_once_with('/crews/')
    
    def test_crew_permission_required_missing_crew_param(self):
        """Test decorator when crew parameter is missing."""
        @crew_permission_required('create')
        def test_view(request, other_param):
            return f"Success"
        
        request = self.factory.get('/test/')
        request.user = self.owner
        request = self.add_session_and_messages(request)
        
        with self.assertRaises(CrewNotFoundError):
            test_view(request, other_param='something')
    
    def test_convenience_decorators(self):
        """Test convenience decorators for specific permissions."""
        from crews.permissions import (
            crew_create_permission_required,
            crew_edit_permission_required,
            crew_publish_permission_required,
            crew_delegate_permission_required
        )
        
        @crew_create_permission_required()
        def create_view(request, crew_slug):
            return "create"
        
        @crew_edit_permission_required()
        def edit_view(request, crew_slug):
            return "edit"
        
        @crew_publish_permission_required()
        def publish_view(request, crew_slug):
            return "publish"
        
        @crew_delegate_permission_required()
        def delegate_view(request, crew_slug):
            return "delegate"
        
        request = self.factory.get('/test/')
        request.user = self.owner
        request = self.add_session_and_messages(request)
        
        # All should work for owner
        self.assertEqual(create_view(request, crew_slug='test-crew'), "create")
        self.assertEqual(edit_view(request, crew_slug='test-crew'), "edit")
        self.assertEqual(publish_view(request, crew_slug='test-crew'), "publish")
        self.assertEqual(delegate_view(request, crew_slug='test-crew'), "delegate")


class PermissionMixinsTestCase(TestCase):
    """Test cases for permission mixins."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.owner = User.objects.create_user('owner', 'owner@test.com', 'password')
        self.member = User.objects.create_user('member', 'member@test.com', 'password')
        
        # Create test crew
        self.crew = Crew.objects.create(
            name='Test Crew',
            slug='test-crew',
            description='A test crew for permissions testing'
        )
        
        # Create memberships
        CrewMembership.objects.create(crew=self.crew, user=self.owner, role='OWNER')
        CrewMembership.objects.create(crew=self.crew, user=self.member, role='MEMBER')
    
    def add_session_and_messages(self, request):
        """Add session and messages support to request."""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        request._messages = messages
        return request
    
    def test_crew_permission_mixin_success(self):
        """Test mixin when user has permission."""
        class TestView(CrewPermissionMixin):
            required_crew_permission = 'create'
            
            def get(self, request, crew_slug):
                return f"Success for {crew_slug}"
        
        view = TestView()
        request = self.factory.get('/test/')
        request.user = self.owner
        request = self.add_session_and_messages(request)
        
        # Mock the super().dispatch call
        with patch.object(CrewPermissionMixin.__bases__[0], 'dispatch') as mock_super:
            mock_super.return_value = "mocked_response"
            result = view.dispatch(request, crew_slug='test-crew')
            mock_super.assert_called_once()
    
    def test_crew_permission_mixin_insufficient_permission(self):
        """Test mixin when user lacks permission."""
        class TestView(CrewPermissionMixin):
            required_crew_permission = 'create'
            
            def get(self, request, crew_slug):
                return f"Success for {crew_slug}"
        
        view = TestView()
        request = self.factory.get('/test/')
        request.user = self.member
        request = self.add_session_and_messages(request)
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request, crew_slug='test-crew')
    
    def test_crew_permission_mixin_get_crew_methods(self):
        """Test mixin methods for getting crew and membership."""
        class TestView(CrewPermissionMixin):
            required_crew_permission = 'create'
            
            def get(self, request, crew_slug):
                return f"Success for {crew_slug}"
        
        view = TestView()
        view.kwargs = {'crew_slug': 'test-crew'}
        view.request = Mock()
        view.request.user = self.owner
        
        # Test get_crew_identifier
        self.assertEqual(view.get_crew_identifier(), 'test-crew')
        
        # Test get_crew_membership
        membership = view.get_crew_membership()
        self.assertEqual(membership.user, self.owner)
        self.assertEqual(membership.crew, self.crew)
        
        # Test get_crew
        crew = view.get_crew()
        self.assertEqual(crew, self.crew)
    
    def test_crew_permission_mixin_missing_permission_setting(self):
        """Test mixin when required_crew_permission is not set."""
        class TestView(CrewPermissionMixin):
            # required_crew_permission not set
            
            def get(self, request, crew_slug):
                return f"Success for {crew_slug}"
        
        view = TestView()
        request = self.factory.get('/test/')
        request.user = self.owner
        request = self.add_session_and_messages(request)
        
        with self.assertRaises(NotImplementedError):
            view.dispatch(request, crew_slug='test-crew')
    
    def test_specific_permission_mixins(self):
        """Test specific permission mixins."""
        from crews.permissions import (
            CrewCreatePermissionMixin,
            CrewEditPermissionMixin,
            CrewPublishPermissionMixin,
            CrewDelegatePermissionMixin
        )
        
        # Test that each mixin has the correct permission set
        create_mixin = CrewCreatePermissionMixin()
        self.assertEqual(create_mixin.required_crew_permission, 'create')
        
        edit_mixin = CrewEditPermissionMixin()
        self.assertEqual(edit_mixin.required_crew_permission, 'edit')
        
        publish_mixin = CrewPublishPermissionMixin()
        self.assertEqual(publish_mixin.required_crew_permission, 'publish')
        
        delegate_mixin = CrewDelegatePermissionMixin()
        self.assertEqual(delegate_mixin.required_crew_permission, 'delegate')
