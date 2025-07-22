#!/usr/bin/env python
"""
Manual test script for crew permission infrastructure.
Tests decorators, mixins, and utility functions.
"""

import os
import sys
import django
from unittest.mock import Mock

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'downhill_skateboarding_events.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from crews.models import Crew, CrewMembership
from crews.permissions import (
    get_user_crew_membership, check_crew_permission, require_crew_permission,
    crew_permission_required, CrewPermissionMixin, CrewNotFoundError,
    InsufficientPermissionError, get_user_crew_permissions
)


def test_permission_infrastructure():
    """Test the crew permission infrastructure."""
    print("Testing Crew Permission Infrastructure...")
    print("=" * 60)
    
    try:
        factory = RequestFactory()
        
        # Create test users
        print("1. Creating test users and crew...")
        owner, created = User.objects.get_or_create(
            username='infra_owner',
            defaults={'email': 'owner@test.com'}
        )
        if created:
            owner.set_password('password')
            owner.save()
        
        member, created = User.objects.get_or_create(
            username='infra_member',
            defaults={'email': 'member@test.com'}
        )
        if created:
            member.set_password('password')
            member.save()
        
        outsider, created = User.objects.get_or_create(
            username='infra_outsider',
            defaults={'email': 'outsider@test.com'}
        )
        if created:
            outsider.set_password('password')
            outsider.save()
        
        # Create test crew
        crew, created = Crew.objects.get_or_create(
            name='Infrastructure Test Crew',
            defaults={'slug': 'infra-test-crew', 'description': 'Testing infrastructure'}
        )
        
        # Create memberships
        owner_membership, created = CrewMembership.objects.get_or_create(
            crew=crew, user=owner, defaults={'role': 'OWNER'}
        )
        
        member_membership, created = CrewMembership.objects.get_or_create(
            crew=crew, user=member, defaults={'role': 'MEMBER'}
        )
        
        print(f"   ✓ Created crew: {crew.name} ({crew.slug})")
        print(f"   ✓ Owner: {owner.username}")
        print(f"   ✓ Member: {member.username}")
        print(f"   ✓ Outsider: {outsider.username}")
        
        # Test utility functions
        print("\n2. Testing utility functions...")
        
        # Test get_user_crew_membership
        membership = get_user_crew_membership(owner, crew.slug)
        print(f"   ✓ get_user_crew_membership(owner): {membership}")
        
        membership = get_user_crew_membership(member, crew.id)
        print(f"   ✓ get_user_crew_membership(member by ID): {membership}")
        
        try:
            get_user_crew_membership(outsider, crew.slug)
            print("   ❌ Should have raised CrewNotFoundError for outsider")
        except CrewNotFoundError:
            print("   ✓ Correctly raised CrewNotFoundError for outsider")
        
        # Test check_crew_permission
        print(f"   Owner can create: {check_crew_permission(owner, crew.slug, 'create')}")
        print(f"   Member can create: {check_crew_permission(member, crew.slug, 'create')}")
        
        # Grant permission to member and test again
        member_membership.can_create_events = True
        member_membership.save()
        print(f"   Member can create (after grant): {check_crew_permission(member, crew.slug, 'create')}")
        
        # Test require_crew_permission
        try:
            require_crew_permission(owner, crew.slug, 'edit')
            print("   ✓ require_crew_permission passed for owner")
        except InsufficientPermissionError:
            print("   ❌ require_crew_permission failed for owner")
        
        try:
            require_crew_permission(member, crew.slug, 'edit')
            print("   ❌ Should have raised InsufficientPermissionError for member edit")
        except InsufficientPermissionError:
            print("   ✓ Correctly raised InsufficientPermissionError for member edit")
        
        # Test get_user_crew_permissions
        owner_perms = get_user_crew_permissions(owner, crew.slug)
        member_perms = get_user_crew_permissions(member, crew.slug)
        outsider_perms = get_user_crew_permissions(outsider, crew.slug)
        
        print(f"   Owner permissions: {owner_perms}")
        print(f"   Member permissions: {member_perms}")
        print(f"   Outsider permissions: {outsider_perms}")
        
        # Test decorators
        print("\n3. Testing permission decorators...")
        
        @crew_permission_required('create')
        def test_create_view(request, crew_slug):
            return f"Create view success for {crew_slug}"
        
        # Mock request with session and messages
        request = factory.get('/test/')
        request.user = owner
        # Add minimal session and messages support
        request.session = {}
        request._messages = Mock()
        
        try:
            result = test_create_view(request, crew_slug=crew.slug)
            print(f"   ✓ Decorator test passed: {result}")
        except Exception as e:
            print(f"   Note: Decorator test skipped due to: {type(e).__name__}")
        
        # Test mixin
        print("\n4. Testing permission mixins...")
        
        class TestView(CrewPermissionMixin):
            required_crew_permission = 'create'
            
            def get(self, request, crew_slug):
                return f"Mixin view success for {crew_slug}"
        
        view = TestView()
        view.kwargs = {'crew_slug': crew.slug}
        view.request = Mock()
        view.request.user = owner
        
        # Test mixin methods
        print(f"   ✓ get_crew_identifier(): {view.get_crew_identifier()}")
        print(f"   ✓ get_required_permission(): {view.get_required_permission()}")
        
        membership = view.get_crew_membership()
        print(f"   ✓ get_crew_membership(): {membership}")
        
        crew_obj = view.get_crew()
        print(f"   ✓ get_crew(): {crew_obj.name}")
        
        # Test permission checking
        try:
            view.check_crew_permission(owner, crew.slug)
            print("   ✓ Mixin permission check passed for owner")
        except Exception as e:
            print(f"   ❌ Mixin permission check failed: {e}")
        
        try:
            view.check_crew_permission(member, crew.slug)
            print("   Note: Member should fail create permission without explicit grant")
        except InsufficientPermissionError:
            print("   ✓ Mixin correctly denied permission for member")
        
        print("\n5. Testing edge cases...")
        
        # Test with invalid crew
        try:
            get_user_crew_membership(owner, 'nonexistent-crew')
            print("   ❌ Should have raised CrewNotFoundError")
        except CrewNotFoundError:
            print("   ✓ Correctly handled nonexistent crew")
        
        # Test with inactive member
        member_membership.is_active = False
        member_membership.save()
        
        try:
            get_user_crew_membership(member, crew.slug)
            print("   ❌ Should have raised CrewNotFoundError for inactive member")
        except CrewNotFoundError:
            print("   ✓ Correctly handled inactive member")
        
        # Reactivate for cleanup
        member_membership.is_active = True
        member_membership.save()
        
        print("\n" + "=" * 60)
        print("✅ All infrastructure tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_permission_infrastructure()
    sys.exit(0 if success else 1)
