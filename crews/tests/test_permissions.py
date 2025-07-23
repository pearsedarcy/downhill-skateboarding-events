"""
Tests for crew permissions functionality.

Tests the permission system for event management within crews,
including permission checking, delegation, and role-based access.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from crews.models import Crew, CrewMembership, CrewActivity


class CrewPermissionsTestCase(TestCase):
    """Test cases for crew permission functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.owner = User.objects.create_user('owner', 'owner@test.com', 'password')
        self.admin = User.objects.create_user('admin', 'admin@test.com', 'password')
        self.event_manager = User.objects.create_user('event_manager', 'em@test.com', 'password')
        self.member = User.objects.create_user('member', 'member@test.com', 'password')
        self.outsider = User.objects.create_user('outsider', 'outsider@test.com', 'password')
        
        # Create test crew
        self.crew = Crew.objects.create(
            name='Test Crew',
            description='A test crew for permissions testing'
        )
        
        # Create memberships
        self.owner_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.owner,
            role='OWNER'
        )
        
        self.admin_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.admin,
            role='ADMIN'
        )
        
        self.event_manager_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.event_manager,
            role='EVENT_MANAGER'
        )
        
        self.member_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=self.member,
            role='MEMBER'
        )
    
    def test_role_based_permissions(self):
        """Test that owners and admins have all permissions by default."""
        # Owners should have all permissions
        self.assertTrue(self.owner_membership.has_event_permission('create'))
        self.assertTrue(self.owner_membership.has_event_permission('edit'))
        self.assertTrue(self.owner_membership.has_event_permission('publish'))
        self.assertTrue(self.owner_membership.has_event_permission('delegate'))
        
        # Admins should have all permissions
        self.assertTrue(self.admin_membership.has_event_permission('create'))
        self.assertTrue(self.admin_membership.has_event_permission('edit'))
        self.assertTrue(self.admin_membership.has_event_permission('publish'))
        self.assertTrue(self.admin_membership.has_event_permission('delegate'))
        
        # Regular members should have no permissions by default
        self.assertFalse(self.member_membership.has_event_permission('create'))
        self.assertFalse(self.member_membership.has_event_permission('edit'))
        self.assertFalse(self.member_membership.has_event_permission('publish'))
        self.assertFalse(self.member_membership.has_event_permission('delegate'))
    
    def test_specific_permission_granting(self):
        """Test granting specific permissions to members."""
        # Grant create permission to member
        self.member_membership.grant_permission('create', self.owner)
        
        # Check that only create permission is granted
        self.assertTrue(self.member_membership.has_event_permission('create'))
        self.assertFalse(self.member_membership.has_event_permission('edit'))
        self.assertFalse(self.member_membership.has_event_permission('publish'))
        self.assertFalse(self.member_membership.has_event_permission('delegate'))
        
        # Grant multiple permissions
        self.member_membership.grant_permission('edit', self.admin)
        self.member_membership.grant_permission('publish', self.owner)
        
        self.assertTrue(self.member_membership.has_event_permission('create'))
        self.assertTrue(self.member_membership.has_event_permission('edit'))
        self.assertTrue(self.member_membership.has_event_permission('publish'))
        self.assertFalse(self.member_membership.has_event_permission('delegate'))
    
    def test_permission_revocation(self):
        """Test revoking permissions from members."""
        # First grant permissions
        self.member_membership.can_create_events = True
        self.member_membership.can_edit_events = True
        self.member_membership.save()
        
        # Verify they have permissions
        self.assertTrue(self.member_membership.has_event_permission('create'))
        self.assertTrue(self.member_membership.has_event_permission('edit'))
        
        # Revoke create permission
        self.member_membership.revoke_permission('create', self.admin)
        
        # Check that only create permission is revoked
        self.assertFalse(self.member_membership.has_event_permission('create'))
        self.assertTrue(self.member_membership.has_event_permission('edit'))
    
    def test_delegation_permissions(self):
        """Test permission delegation rules."""
        # Owner should be able to delegate to everyone except other owners
        self.assertTrue(self.owner_membership.can_delegate_to_member(self.admin_membership))
        self.assertTrue(self.owner_membership.can_delegate_to_member(self.event_manager_membership))
        self.assertTrue(self.owner_membership.can_delegate_to_member(self.member_membership))
        
        # Create another owner to test owner-to-owner delegation
        other_owner = User.objects.create_user('owner2', 'owner2@test.com', 'password')
        other_owner_membership = CrewMembership.objects.create(
            crew=self.crew,
            user=other_owner,
            role='OWNER'
        )
        self.assertFalse(self.owner_membership.can_delegate_to_member(other_owner_membership))
        
        # Admin should be able to delegate to event managers and members
        self.assertTrue(self.admin_membership.can_delegate_to_member(self.event_manager_membership))
        self.assertTrue(self.admin_membership.can_delegate_to_member(self.member_membership))
        self.assertFalse(self.admin_membership.can_delegate_to_member(self.owner_membership))
        
        # Members without delegation permission should not be able to delegate
        self.assertFalse(self.member_membership.can_delegate_to_member(self.event_manager_membership))
        
        # Grant delegation permission and test again
        self.member_membership.can_delegate_permissions = True
        self.member_membership.save()
        # Still shouldn't be able to delegate due to role hierarchy
        self.assertFalse(self.member_membership.can_delegate_to_member(self.event_manager_membership))
    
    def test_crew_permission_methods(self):
        """Test crew-level permission checking methods."""
        # Test with owner
        self.assertTrue(self.crew.can_create_events(self.owner))
        self.assertTrue(self.crew.can_edit_events(self.owner))
        self.assertTrue(self.crew.can_publish_events(self.owner))
        self.assertTrue(self.crew.can_delegate_permissions(self.owner))
        
        # Test with member (no permissions)
        self.assertFalse(self.crew.can_create_events(self.member))
        self.assertFalse(self.crew.can_edit_events(self.member))
        self.assertFalse(self.crew.can_publish_events(self.member))
        self.assertFalse(self.crew.can_delegate_permissions(self.member))
        
        # Test with outsider (not a member)
        self.assertFalse(self.crew.can_create_events(self.outsider))
        self.assertFalse(self.crew.can_edit_events(self.outsider))
        self.assertFalse(self.crew.can_publish_events(self.outsider))
        self.assertFalse(self.crew.can_delegate_permissions(self.outsider))
        
        # Grant specific permission and test
        self.member_membership.can_create_events = True
        self.member_membership.save()
        self.assertTrue(self.crew.can_create_events(self.member))
        self.assertFalse(self.crew.can_edit_events(self.member))
    
    def test_permission_summary(self):
        """Test the permission summary method."""
        # Test for owner (should have all permissions via role)
        summary = self.owner_membership.get_permission_summary()
        self.assertTrue(summary['create'])
        self.assertTrue(summary['edit'])
        self.assertTrue(summary['publish'])
        self.assertTrue(summary['delegate'])
        self.assertTrue(summary['role_based'])
        
        # Test for member with specific permissions
        self.member_membership.can_create_events = True
        self.member_membership.can_publish_events = True
        self.member_membership.save()
        
        summary = self.member_membership.get_permission_summary()
        self.assertTrue(summary['create'])
        self.assertFalse(summary['edit'])
        self.assertTrue(summary['publish'])
        self.assertFalse(summary['delegate'])
        self.assertFalse(summary['role_based'])
    
    def test_activity_logging(self):
        """Test that permission changes are logged as activities."""
        initial_activity_count = CrewActivity.objects.count()
        
        # Grant a permission
        self.member_membership.grant_permission('create', self.owner)
        
        # Check that activity was logged
        self.assertEqual(CrewActivity.objects.count(), initial_activity_count + 1)
        
        activity = CrewActivity.objects.latest('created_at')
        self.assertEqual(activity.crew, self.crew)
        self.assertEqual(activity.user, self.owner)
        self.assertEqual(activity.target_user, self.member)
        self.assertIn('create', activity.description)
        self.assertEqual(activity.metadata['permission_type'], 'create')
        self.assertEqual(activity.metadata['action'], 'granted')
        
        # Revoke a permission
        self.member_membership.revoke_permission('create', self.admin)
        
        # Check that revocation was logged
        self.assertEqual(CrewActivity.objects.count(), initial_activity_count + 2)
        
        activity = CrewActivity.objects.latest('created_at')
        self.assertEqual(activity.user, self.admin)
        self.assertEqual(activity.target_user, self.member)
        self.assertIn('create', activity.description)
        self.assertEqual(activity.metadata['action'], 'revoked')
    
    def test_inactive_member_permissions(self):
        """Test that inactive members have no permissions."""
        # Grant permissions to member
        self.member_membership.can_create_events = True
        self.member_membership.can_edit_events = True
        self.member_membership.save()
        
        # Verify permissions work when active
        self.assertTrue(self.member_membership.has_event_permission('create'))
        self.assertTrue(self.member_membership.has_event_permission('edit'))
        
        # Deactivate membership
        self.member_membership.is_active = False
        self.member_membership.save()
        
        # Verify no permissions when inactive
        self.assertFalse(self.member_membership.has_event_permission('create'))
        self.assertFalse(self.member_membership.has_event_permission('edit'))
    
    def test_get_user_membership(self):
        """Test the crew's get_user_membership method."""
        # Test existing member
        membership = self.crew.get_user_membership(self.owner)
        self.assertEqual(membership, self.owner_membership)
        
        # Test non-member
        membership = self.crew.get_user_membership(self.outsider)
        self.assertIsNone(membership)
        
        # Test inactive member
        self.member_membership.is_active = False
        self.member_membership.save()
        membership = self.crew.get_user_membership(self.member)
        self.assertIsNone(membership)
